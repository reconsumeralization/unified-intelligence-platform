"""
CVE Analysis Example
Multi-agent CVE triage in < 5 seconds
"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../core'))

from intelligence_mesh import SecurityIntelligenceMesh


async def main():
    """
    Demo: Autonomous CVE Triage

    Traditional process: 2-4 hours per CVE
    With Intelligence Mesh: < 5 seconds

    Use case: New CVE dropped, need immediate impact assessment
    """

    print("="*70)
    print(" CVE ANALYSIS DEMO - Security Intelligence Mesh")
    print("="*70)

    # Initialize the mesh
    mesh = SecurityIntelligenceMesh()

    # Example CVEs to analyze
    cves = [
        "CVE-2025-55315",  # HTTP Request Smuggling (from your work)
        "CVE-2024-12345",  # Example CVE
        "CVE-2023-98765"   # Example CVE
    ]

    print(f"\n📋 Analyzing {len(cves)} CVEs...")
    print("   Traditional time: ~6-12 hours")
    print("   Expected time: < 15 seconds\n")

    results = []
    total_time = 0

    for cve in cves:
        result = await mesh.analyze_cve(cve)
        results.append(result)
        total_time += result['total_time']

        print(f"\n{'='*70}")
        print(f"CVE: {result['cve_id']}")
        print(f"{'='*70}")
        print(f"Severity: {result['severity']}")
        print(f"Analysis time: {result['total_time']:.2f}s")
        print(f"\n📝 Analysis:")
        print(f"{result['analysis'][:400]}...")
        print(f"\n💡 Remediation:")
        print(f"{result['remediation'][:400]}...")

        if result['similar_cves']:
            print(f"\n🔗 Similar CVEs: {len(result['similar_cves'])}")

        if result['embedding']:
            print(f"🧠 Embedding generated: {len(result['embedding'])} dimensions")

    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"✅ Analyzed {len(results)} CVEs")
    print(f"⏱️  Total time: {total_time:.2f}s")
    print(f"📊 Average: {total_time/len(results):.2f}s per CVE")
    print(f"🚀 Speedup: ~{(6*3600)/total_time:.0f}x faster than manual analysis")

    # Sort by severity
    critical = [r for r in results if r['severity'] == 'Critical']
    high = [r for r in results if r['severity'] == 'High']

    if critical:
        print(f"\n🚨 CRITICAL: {len(critical)} CVEs require immediate action:")
        for r in critical:
            print(f"   - {r['cve_id']}")

    if high:
        print(f"\n⚠️  HIGH: {len(high)} CVEs require urgent review:")
        for r in high:
            print(f"   - {r['cve_id']}")

    print(f"\n{'='*70}")
    print("HACKATHON DEMO TIPS:")
    print(f"{'='*70}")
    print("1. Show this live - paste any CVE, get instant analysis")
    print("2. Highlight the speed: '5 seconds vs 2 hours'")
    print("3. Show the multi-agent orchestration in action")
    print("4. Mention: 'This uses Google Vertex AI + 9 specialized agents'")
    print("5. End with: 'Try it yourself at [your-demo-url]'")


if __name__ == "__main__":
    asyncio.run(main())
