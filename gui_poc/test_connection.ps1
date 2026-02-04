# ============================================
# Photo Tool - Connection Test
# ============================================
# Tests network connectivity for Smart TV
# No Administrator rights needed
# ============================================

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "📺 Photo Tool - Smart TV Connection Test" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Get local IP
Write-Host "Step 1: Finding your PC's IP address..." -ForegroundColor Yellow
Write-Host ""

$networkAdapters = Get-NetIPAddress -AddressFamily IPv4 | Where-Object {
    $_.InterfaceAlias -like '*Wi-Fi*' -or 
    $_.InterfaceAlias -like '*Ethernet*' -or 
    $_.InterfaceAlias -like '*WLAN*'
}

if ($networkAdapters) {
    Write-Host "Found network adapter(s):" -ForegroundColor Green
    foreach ($adapter in $networkAdapters) {
        Write-Host "  Interface: $($adapter.InterfaceAlias)" -ForegroundColor White
        Write-Host "  IP Address: $($adapter.IPAddress)" -ForegroundColor Cyan
        Write-Host ""
    }
    
    $localIP = $networkAdapters[0].IPAddress
} else {
    Write-Host "❌ No active network connection found!" -ForegroundColor Red
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Step 2: Check firewall rule
Write-Host ""
Write-Host "Step 2: Checking firewall configuration..." -ForegroundColor Yellow

$firewallRule = Get-NetFirewallRule -DisplayName "Photo Tool Web GUI" -ErrorAction SilentlyContinue

if ($firewallRule) {
    if ($firewallRule.Enabled -eq 'True') {
        Write-Host "✓ Firewall rule exists and is enabled" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Firewall rule exists but is DISABLED" -ForegroundColor Yellow
    }
} else {
    Write-Host "❌ Firewall rule does NOT exist!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please run setup_firewall.ps1 as Administrator first!" -ForegroundColor Yellow
}

Write-Host ""

# Step 3: Check if server is running
Write-Host "Step 3: Checking if server is running..." -ForegroundColor Yellow

$serverRunning = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue

if ($serverRunning) {
    Write-Host "✓ Server is running on port 8000" -ForegroundColor Green
    Write-Host ""
    Write-Host "Server details:" -ForegroundColor White
    Write-Host "  Local Address: $($serverRunning.LocalAddress)" -ForegroundColor Cyan
    Write-Host "  Local Port: $($serverRunning.LocalPort)" -ForegroundColor Cyan
    Write-Host "  Process ID: $($serverRunning.OwningProcess)" -ForegroundColor Cyan
} else {
    Write-Host "❌ Server is NOT running!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Start the server with:" -ForegroundColor Yellow
    Write-Host "  cd C:\_Git\Python-tools" -ForegroundColor Cyan
    Write-Host "  python gui_poc/server.py" -ForegroundColor Cyan
}

Write-Host ""

# Step 4: Test localhost connection
Write-Host "Step 4: Testing localhost connection..." -ForegroundColor Yellow

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✓ Localhost connection successful (Status: $($response.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "❌ Cannot connect to localhost:8000" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Step 5: Test network IP connection
Write-Host "Step 5: Testing network IP connection..." -ForegroundColor Yellow

try {
    $response = Invoke-WebRequest -Uri "http://${localIP}:8000/" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✓ Network IP connection successful (Status: $($response.StatusCode))" -ForegroundColor Green
    Write-Host "  Smart TV should be able to connect!" -ForegroundColor Green
} catch {
    Write-Host "❌ Cannot connect to ${localIP}:8000" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "Possible issues:" -ForegroundColor Yellow
    Write-Host "  1. Server is not running" -ForegroundColor White
    Write-Host "  2. Firewall is blocking the connection" -ForegroundColor White
    Write-Host "  3. Server is not bound to 0.0.0.0" -ForegroundColor White
}

Write-Host ""

# Summary
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "📊 CONNECTION TEST SUMMARY" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

$allGood = $true

if ($localIP) {
    Write-Host "✓ Network Adapter: OK" -ForegroundColor Green
} else {
    Write-Host "❌ Network Adapter: FAILED" -ForegroundColor Red
    $allGood = $false
}

if ($firewallRule -and $firewallRule.Enabled -eq 'True') {
    Write-Host "✓ Firewall Rule: OK" -ForegroundColor Green
} else {
    Write-Host "❌ Firewall Rule: MISSING or DISABLED" -ForegroundColor Red
    $allGood = $false
}

if ($serverRunning) {
    Write-Host "✓ Server Running: OK" -ForegroundColor Green
} else {
    Write-Host "❌ Server Running: NO" -ForegroundColor Red
    $allGood = $false
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

if ($allGood) {
    Write-Host "🎉 EVERYTHING LOOKS GOOD!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Smart TV Access URL:" -ForegroundColor White
    Write-Host "  http://$localIP:8000" -ForegroundColor Green
    Write-Host ""
    Write-Host "Open this URL in your Smart TV browser!" -ForegroundColor Yellow
} else {
    Write-Host "⚠️  SOME ISSUES DETECTED" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Fix the issues above and run this test again." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

Read-Host "Press Enter to exit"
