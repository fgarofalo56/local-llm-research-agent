#!/bin/bash
# Test script to verify Ollama connectivity from Docker containers
# Usage: Run this script from inside a Docker container to test host connectivity

echo "Testing Ollama connectivity from Docker container..."
echo ""

# Test 1: Resolve host.docker.internal
echo "1. Testing DNS resolution for host.docker.internal..."
if ping -c 1 host.docker.internal > /dev/null 2>&1; then
    echo "   ✓ host.docker.internal resolves to: $(getent hosts host.docker.internal | awk '{print $1}')"
else
    echo "   ✗ Cannot resolve host.docker.internal"
fi
echo ""

# Test 2: Test Ollama API endpoint
echo "2. Testing Ollama API at http://host.docker.internal:11434..."
if curl -s -f http://host.docker.internal:11434/api/tags > /dev/null 2>&1; then
    echo "   ✓ Ollama API is accessible"
    echo ""
    echo "3. Available models:"
    curl -s http://host.docker.internal:11434/api/tags | python3 -c "import sys, json; models = json.load(sys.stdin)['models']; print('\n'.join(['   - ' + m['name'] for m in models]))"
else
    echo "   ✗ Cannot reach Ollama API"
    echo ""
    echo "Troubleshooting:"
    echo "  - Ensure Ollama is running on the host: ollama list"
    echo "  - Check Ollama is listening on all interfaces (0.0.0.0:11434)"
    echo "  - Verify Docker Desktop allows host.docker.internal connections"
fi
echo ""
echo "Test complete."
