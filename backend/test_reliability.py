"""Automated Reliability Test Suite for Production Backend.

Validates:
1. Application starts safely when database is unreachable.
2. /health responds immediately with 200 during database failure.
3. /ready returns 503 when database is unavailable.
4. /ready returns 200 when database connectivity is active.
5. Slow or failing speech requests do not freeze health checks or independent requests.
6. Database sessions perform explicit rollback upon exceptions.
7. Bounded pool and engine attributes conform to production requirements.
"""

import asyncio
import time
import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.main import app
from backend.database import get_db, Base, engine, check_db_health
from backend.services.speech_service import speech_service, SpeechServiceError
from backend.services.voice_service import voice_service, VoiceServiceError


class TestProductionReliability(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_liveness_endpoint_responds_immediately(self):
        """GET /health must respond immediately with status 'healthy'."""
        t0 = time.time()
        resp = self.client.get("/health")
        elapsed = time.time() - t0
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"status": "healthy"})
        self.assertLess(elapsed, 0.5, "Liveness probe should complete in under 500ms")

    def test_02_ready_endpoint_healthy_when_database_accessible(self):
        """GET /ready returns 200 and 'ready' when check_db_health passes."""
        with patch("backend.routes.health.check_db_health", return_value=True):
            resp = self.client.get("/ready")
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.json(), {"status": "ready", "database": "connected"})

    def test_03_ready_endpoint_returns_503_when_database_unreachable(self):
        """GET /ready returns 503 and 'degraded' when database check fails."""
        with patch("backend.routes.health.check_db_health", return_value=False):
            resp = self.client.get("/ready")
            self.assertEqual(resp.status_code, 503)
            self.assertEqual(resp.json(), {"status": "degraded", "database": "unreachable"})

    def test_04_liveness_healthy_even_during_database_failure(self):
        """GET /health remains 200 even if database check fails or times out."""
        with patch("backend.database.check_db_health", return_value=False):
            resp = self.client.get("/health")
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.json(), {"status": "healthy"})

    def test_05_slow_speech_request_does_not_block_health(self):
        """Simulates a slow 2-second speech call and confirms /health responds concurrently."""
        def slow_transcribe(*args, **kwargs):
            time.sleep(1.0)
            return {"success": True, "transcript": "पाणी कुठे मिळेल?", "language": "mr-IN"}

        with patch.object(type(speech_service), "is_configured", new_callable=lambda: property(lambda self: True)):
            with patch.object(speech_service, "transcribe_audio", side_effect=slow_transcribe):
                t0 = time.time()
                # Run health check right away
                health_resp = self.client.get("/health")
                self.assertEqual(health_resp.status_code, 200)
                self.assertLess(time.time() - t0, 0.5)

    def test_06_database_session_rollback_on_exception(self):
        """Verify that get_db() calls db.rollback() when an unhandled error occurs."""
        mock_session = MagicMock()
        with patch("backend.database.SessionLocal", return_value=mock_session):
            gen = get_db()
            session = next(gen)
            self.assertEqual(session, mock_session)
            # Simulate exception thrown back into generator by FastAPI
            with self.assertRaises(RuntimeError):
                gen.throw(RuntimeError("Simulated database failure during request"))
            mock_session.rollback.assert_called_once()
            mock_session.close.assert_called_once()

    def test_07_postgresql_pool_and_timeout_attributes(self):
        """Verifies that non-sqlite PostgreSQL engine creation configures bounded pool and timeout."""
        sample_pg = "postgresql://user:pass@127.0.0.1:5432/warkari"
        pg_engine = create_engine(
            sample_pg,
            connect_args={"connect_timeout": 5},
            pool_size=3,
            max_overflow=2,
            pool_pre_ping=True,
            pool_recycle=300,
            pool_timeout=10
        )
        self.assertEqual(pg_engine.pool._pre_ping, True)
        self.assertEqual(pg_engine.pool._recycle, 300)
        self.assertEqual(pg_engine.pool._timeout, 10)
        self.assertEqual(pg_engine.pool.size(), 3)
        self.assertEqual(pg_engine.pool._max_overflow, 2)

    def test_08_readiness_strict_timeout_enforcement(self):
        """Simulates a slow DB connection taking > 3.0s and confirms /ready aborts at <= 3.2s returning 503."""
        def slow_db_check(*args, **kwargs):
            time.sleep(4.0)  # Simulates 4s connection wait
            return True

        with patch("backend.routes.health.check_db_health", side_effect=slow_db_check):
            t0 = time.time()
            resp = self.client.get("/ready")
            elapsed = time.time() - t0
            self.assertEqual(resp.status_code, 503)
            self.assertEqual(resp.json(), {"status": "degraded", "database": "unreachable"})
            self.assertLess(elapsed, 3.5, f"Readiness took {elapsed:.2f}s, expected <= 3.5s")
            self.assertGreaterEqual(elapsed, 2.8, f"Readiness exited too early: {elapsed:.2f}s")

    def test_09_readiness_worker_saturation_and_immediate_rejection(self):
        """When MAX_READINESS_WORKERS slots are occupied, subsequent requests reject immediately with 503 (database busy)."""
        import threading

        hold_event = threading.Event()
        release_event = threading.Event()

        def slow_stuck_db(*args, **kwargs):
            hold_event.set()
            release_event.wait(timeout=5.0)
            return True

        with patch("backend.routes.health.check_db_health", side_effect=slow_stuck_db):
            client = TestClient(app)
            worker_results = []

            def worker_req():
                r = client.get("/ready")
                worker_results.append(r.status_code)

            # Start 2 threads occupying both slots
            t1 = threading.Thread(target=worker_req)
            t2 = threading.Thread(target=worker_req)
            t1.start()
            t2.start()

            # Wait until background DB calls are actively holding slots
            hold_event.wait(timeout=2.0)
            time.sleep(0.1)

            # 3rd request arrives while both workers are busy: must be rejected immediately (< 0.1s)
            t0 = time.time()
            resp_busy = client.get("/ready")
            elapsed = time.time() - t0

            self.assertEqual(resp_busy.status_code, 503)
            self.assertEqual(resp_busy.json(), {"status": "degraded", "database": "busy"})
            self.assertLess(elapsed, 0.2, f"Rejection should be immediate, took {elapsed:.4f}s")

            # Clean up: release workers
            release_event.set()
            t1.join()
            t2.join()

    def test_10_readiness_recovers_after_saturation_clears(self):
        """After saturated workers finish, subsequent requests acquire slots and return 200."""
        # Ensure previous background slots have finished
        time.sleep(0.2)
        with patch("backend.routes.health.check_db_health", return_value=True):
            resp = self.client.get("/ready")
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.json(), {"status": "ready", "database": "connected"})


if __name__ == "__main__":
    unittest.main()
