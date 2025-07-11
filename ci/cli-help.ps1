<#
    Generate CLI help files from Click online help.
    These will get picked up by Sphinx.
 #>
$main = "mav"
$commands = @(
    "positions",
    "tidytiff",
    "totiff",
)

$dst = "$($PSScriptRoot)\..\docs\includes\cli"

# & $main --help | Out-File $(Join-Path $dst cli.${main}.txt)

ForEach ($command in $commands)
{
    Write-Host "Writing help for $command"
    $path = Join-Path $dst cli.${command}.txt
    & $main ${command} --help | Out-File $path
}
