
$srcdir = 'd:\projects\example\example-rgb'
$dstdir = 'd:\projects\example\example-int'

$srcfiles = (Get-ChildItem -Path $srcdir -Filter "*_T.JPG").Fullname

ForEach ($srcfile in $srcfiles)
{
    $base = Split-Path $srcfile -LeafBase; 
    $dstfile = Join-Path -Path $dstdir -ChildPath $($base + '.tif');

	# copy xmp as a block from onefile to another
	# https://exiftool.org/faq.html#Q9
	# & "exiftool" -tagsfromfile $srcfile -xmp $dstfile

    # rebuilds the metadata
    # https://exiftool.org/faq.html#Q20
    & "exiftool" -exif:all= -tagsfromfile $srcfile -exif:all -unsafe -thumbnailimage -xmp -F $dstfile
}

