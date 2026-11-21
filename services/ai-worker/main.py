"""AI Worker Entrypoint [M2]."""
import time
import os

def main():
    print("[AI Worker] Initialized video processing worker...")
    print(f"[AI Worker] Listening to streams from: {os.getenv('MEDIAMTX_RTSP_URL', 'rtsp://localhost:8554')}")
    while True:
        # Worker event loop placeholder
        time.sleep(10)

if __name__ == "__main__":
    main()
