$ck = "C:\XboxGames\Starfield\Content\CreationKit.exe"
$log = "C:\Users\max\Projects\Morrowind\ck.txt"
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $ck
$psi.WorkingDirectory = "C:\XboxGames\Starfield\Content"
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.UseShellExecute = $false
$p = [System.Diagnostics.Process]::Start($psi)
$p.PriorityClass = 'High'
$out = $p.StandardOutput.ReadToEnd()
$err = $p.StandardError.ReadToEnd()
"CK started at $(Get-Date)" | Out-File -FilePath $log -Encoding UTF8
$out | Out-File -FilePath $log -Append -Encoding UTF8
$err | Out-File -FilePath $log -Append -Encoding UTF8
$p.WaitForExit()
