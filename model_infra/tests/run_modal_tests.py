#!/usr/bin/env python3
"""
Modal DeepSeek-OCR Stress Testing Helper

This script provides utilities for testing the live Modal DeepSeek-OCR service.
The Modal service is already deployed and running.
"""

import sys
import time
from pathlib import Path

# Live Modal service URL
MODAL_URL = "https://alphaxiv--deepseek-ocr-modal-serve.modal.run"

def check_service_health():
    """Check if the Modal service is healthy"""
    import requests

    try:
        print(f"� Checking service health at {MODAL_URL}...")
        response = requests.get(f"{MODAL_URL}/health", timeout=10)

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Service is healthy: {data}")
            return True
        else:
            print(f"❌ Service returned status {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Failed to connect to service: {e}")
        return False

def test_single_pdf(pdf_path: str, implementation: str = "base"):
    """Test a single PDF file"""
    import requests

    try:
        print(f"🧪 Testing {pdf_path} with {implementation} implementation...")

        with open(pdf_path, 'rb') as f:
            files = {'file': f}
            url = f"{MODAL_URL}/run/{implementation}/pdf"

            start_time = time.time()
            response = requests.post(url, files=files, timeout=300)  # 5 minute timeout
            end_time = time.time()

            latency = end_time - start_time

            if response.status_code == 200:
                result = response.json()
                print(f"✅ Success! Latency: {latency:.2f}s")
                print(f"   Pages processed: {result.get('num_successful', 0)}/{result.get('num_pages', 0)}")
                if 'performance_metrics' in result:
                    perf = result['performance_metrics']
                    print(f"   GPU Memory Peak: {perf.get('gpu_memory_peak_mb', 'N/A')}MB")
                    print(f"   GPU Utilization: {perf.get('gpu_utilization_avg_percent', 'N/A')}%")
                return True
            else:
                print(f"❌ Failed with status {response.status_code}: {response.text}")
                return False

    except Exception as e:
        print(f"❌ Error testing PDF: {e}")
        return False

def run_quick_test():
    """Run a quick test with available PDFs"""
    print("🚀 Running quick test of Modal DeepSeek-OCR service")
    print("=" * 60)

    # Check service health
    if not check_service_health():
        print("❌ Service is not healthy. Cannot run tests.")
        return

    # Find available PDFs
    test_dir = Path(__file__).parent
    pdf_files = list(test_dir.glob("*.pdf"))

    if not pdf_files:
        print("❌ No PDF files found in tests directory")
        return

    print(f"📄 Found {len(pdf_files)} PDF files:")
    for pdf in pdf_files:
        size_mb = pdf.stat().st_size / (1024 * 1024)
        print(f"   {pdf.name} ({size_mb:.1f}MB)")

    # Test each implementation with the smallest PDF
    small_pdf = min(pdf_files, key=lambda x: x.stat().st_size)

    print(f"\n🧪 Testing with {small_pdf.name}...")

    for impl in ['base', 'app']:
        print(f"\n--- Testing {impl.upper()} implementation ---")
        success = test_single_pdf(str(small_pdf), impl)
        if not success:
            print(f"⚠️  {impl.upper()} implementation failed")

    print("\n✅ Quick test complete!")
    print(f"🔗 Service URL: {MODAL_URL}")
    print("📊 Run full stress tests with: python stress_test.py")

def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        run_quick_test()
    else:
        print("🎯 Modal DeepSeek-OCR Testing Helper")
        print("=" * 50)
        print(f"🔗 Live service URL: {MODAL_URL}")
        print()
        print("Usage:")
        print("  python run_modal_tests.py quick    # Run quick health check")
        print("  python stress_test.py             # Run full stress tests")
        print()
        print("The Modal service is already deployed and running!")

if __name__ == "__main__":
    main()