#!/bin/bash
# Peer Exchange Demo - Complete workflow for agent discovery and trust

set -e

echo "=== AI-IQ Passport Peer Exchange Demo ==="
echo ""
echo "This demo shows how agents can discover each other and build trust networks."
echo ""

# Setup
DEMO_DIR="/tmp/passport-demo"
rm -rf "$DEMO_DIR"
mkdir -p "$DEMO_DIR"

echo "Step 1: Generate passports for two agents"
echo "==========================================="
echo ""

# Agent A - Python expert
echo "Creating Agent A (Python expert)..."
ai-iq-passport generate \
  --name "PythonAgent" \
  --agent-id "python-expert-001" \
  --output "$DEMO_DIR/agent_a.json"

ai-iq-passport skill add "Python" \
  --passport "$DEMO_DIR/agent_a.json" \
  --confidence 0.95 \
  --evidence 50

ai-iq-passport skill add "Testing" \
  --passport "$DEMO_DIR/agent_a.json" \
  --confidence 0.85 \
  --evidence 30

ai-iq-passport skill add "API Design" \
  --passport "$DEMO_DIR/agent_a.json" \
  --confidence 0.80 \
  --evidence 20

echo ""

# Agent B - JavaScript expert
echo "Creating Agent B (JavaScript expert)..."
ai-iq-passport generate \
  --name "JSAgent" \
  --agent-id "javascript-expert-002" \
  --output "$DEMO_DIR/agent_b.json"

ai-iq-passport skill add "JavaScript" \
  --passport "$DEMO_DIR/agent_b.json" \
  --confidence 0.92 \
  --evidence 45

ai-iq-passport skill add "React" \
  --passport "$DEMO_DIR/agent_b.json" \
  --confidence 0.88 \
  --evidence 35

ai-iq-passport skill add "WebDev" \
  --passport "$DEMO_DIR/agent_b.json" \
  --confidence 0.85 \
  --evidence 40

echo ""
echo "Step 2: Agent A starts serving its passport"
echo "============================================"
echo ""
echo "In one terminal, run:"
echo "  ai-iq-passport serve --passport $DEMO_DIR/agent_a.json --port 8500"
echo ""
echo "Starting server in background for demo..."

# Start server in background
ai-iq-passport serve --passport "$DEMO_DIR/agent_a.json" --port 8500 > "$DEMO_DIR/server.log" 2>&1 &
SERVER_PID=$!
sleep 2

echo "Server started (PID: $SERVER_PID)"
echo ""

echo "Step 3: Agent B discovers Agent A"
echo "=================================="
echo ""

# Create a temporary home for Agent B's peers
export HOME="$DEMO_DIR/agent_b_home"
mkdir -p "$HOME/.ai-iq-passport/peers"

echo "Agent B fetches Agent A's passport..."
ai-iq-passport fetch http://localhost:8500 --save

echo ""
echo "Step 4: Agent B reviews Agent A's credentials"
echo "=============================================="
echo ""

echo "Agent B lists known peers:"
ai-iq-passport peers

echo ""
echo "Step 5: Agent B decides to trust Agent A"
echo "========================================="
echo ""

ai-iq-passport trust "python-expert-001"

echo ""
echo "Agent B lists peers again (now trusted):"
ai-iq-passport peers

echo ""
echo "Step 6: Full exchange handshake"
echo "================================"
echo ""

echo "Agent B exchanges passports with Agent A..."
ai-iq-passport exchange http://localhost:8500 --passport "$DEMO_DIR/agent_b.json"

echo ""
echo "Step 7: Cleanup"
echo "==============="
echo ""

kill $SERVER_PID 2>/dev/null || true
echo "Server stopped"

echo ""
echo "=== Demo Complete ==="
echo ""
echo "Key files created:"
echo "  Agent A passport: $DEMO_DIR/agent_a.json"
echo "  Agent B passport: $DEMO_DIR/agent_b.json"
echo "  Agent B peers: $HOME/.ai-iq-passport/peers/"
echo ""
echo "Try the commands yourself:"
echo "  1. ai-iq-passport serve --passport <file> --port 8500"
echo "  2. ai-iq-passport fetch http://localhost:8500 --save"
echo "  3. ai-iq-passport trust <agent-id>"
echo "  4. ai-iq-passport peers"
echo "  5. ai-iq-passport exchange http://localhost:8500"
