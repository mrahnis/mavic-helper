
$srcdir = 'd:\projects\example\example-rgb'
$dstdir = 'd:\projects\example\example-int'

$srcfiles = (Get-ChildItem -Path $srcdir -Filter "*_T.JPG").Fullname

ForEach ($srcfile in $srcfiles) {
    $base = Split-Path $srcfile -LeafBase; 
    $dstfile = Join-Path -Path $dstdir -ChildPath $($base + '.tif');

    & "mav" totiff $srcfile $dstfile --altitude hagl --temperature 5 --humidity 30 --dtype uint16
}

<#
# need to use the Using stuff inside here...
$srcfiles | ForEach-Object -Parallel {
    $base = Split-Path $srcfile -LeafBase; 
    $dstfile = Join-Path -Path $dstdir -ChildPath $($base + '.tif');

    & "mav" totiff $srcfile $dstfile --altitude hagl --temperature 5 --humidity 30 --dtype uint16
} -ThrottleLimit 3
#>