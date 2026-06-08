#!/usr/bin/perl -w
###
$gprog="grdtrack";
$gprog="gmt grdtrack";
###
###
(@ARGV==2) or die "$0 Location(Lon,Lat)\n";
($lon,$lat)=@ARGV;
###
if($lon<0){$lon=$lon+360;}
###
$slabdir="/Users/ghayes/Desktop/Slab2.0/Slab2Distribute_Mar2018";
$suppdir="/Users/ghayes/Desktop/Slab2.0/Slab2Distribute_Mar2018/Slab2Supp";
###
@ids=`ls $slabdir/*slab2_dep*.grd | awk -F/ '{print \$NF}' | awk -F_ '{print \$1}'`;
###
$match=0;
foreach(@ids){
$ID=$_;chomp($ID);
$slabmod=`ls $slabdir/$ID\_slab2_str*.grd`;
chomp($slabmod);
$str=`echo $lon $lat | $gprog -G$slabmod -Z`;
$slabmod=`ls $slabdir/$ID\_slab2_dip*.grd`;
chomp($slabmod);
$dip=`echo $lon $lat | $gprog -G$slabmod -Z`;
$slabmod=`ls $slabdir/$ID\_slab2_dep*.grd`;
chomp($slabmod);
$dep=`echo $lon $lat | $gprog -G$slabmod -Z`;
$slabmod=`ls $slabdir/$ID\_slab2_thk*.grd`;
chomp($slabmod);
$thk=`echo $lon $lat | $gprog -G$slabmod -Z`;
$slabmod=`ls $slabdir/$ID\_slab2_unc*.grd`;
chomp($slabmod);
$unc=`echo $lon $lat | $gprog -G$slabmod -Z`;
if(($dep) && ($str) && ($dip)){
    $dep=-$dep;
    chomp($str);chomp($dip);chomp($dep);
    if(($dep==$dep) && ($str==$str) && ($dip==$dip)){
    print "Location falls within $ID slab model\n";
    printf "%-13s %6.2f\n","Slab Depth = ",$dep;
    printf "%-14s %6.2f\n","Slab Strike = ",$str;
    printf "%-11s %5.2f\n","Slab Dip = ",$dip;
    printf "%-17s %5.2f\n","Slab Thickness = ",$thk;
    printf "%-17s %5.2f\n","Slab Depth Unc = ",$unc;
    $id1[$match]=$ID;
    $match++;
    }
}
}
####
# Check Supp Models
if(($lon>0) && ($lat>0)){
     $locstring=sprintf("%6.2f%1s%5.2f",$lon,",",$lat);
} elsif(($lon<0) && ($lat>0)){
     $locstring=sprintf("%7.2f%1s%5.2f",$lon,",",$lat);
} elsif(($lon>0) && ($lat<0)){
     $locstring=sprintf("%6.2f%1s%6.2f",$lon,",",$lat);
} elsif(($lon<0) && ($lat<0)){
     $locstring=sprintf("%7.2f%1s%6.2f",$lon,",",$lat);
}
##
$n=0;
foreach(@id1){
    $id0=$id1[$n];
    if(($id0 eq "izu") || ($id0 eq "ker") || ($id0 eq "man") || ($id0 eq "sol")){
	print "Found Supplementary Slab Data\n";
	$slabmod=`ls $suppdir/$id0\_slab2_sup*.csv`;
	chomp($slabmod);
	@sloc=`grep $locstring $slabmod`;
	$nn=0;
	foreach(@sloc){
	    $cur=$sloc[$nn];
	    ($lon,$lat,$dep1,$str1,$dip1,$dz1,$dz2,$dz3,$th1)=split /,/,"$cur";
	    chomp($th1);chomp($dz2);chomp($dz3);
	    if($nn==0){
	    print "Location falls within supplement to $id0 slab model\n";
	    print "Depth Strike Dip Thickness Uncertainty\n";
	    }
	    printf "%6.2f %6.2f %5.2f %6.2f %6.2f\n",$dep1,$str1,$dip1,$th1,$dz1; 
#	    printf "%-13s %6.2f\n","Slab Depth = ",$dep1;
#    	    printf "%-14s %6.2f\n","Slab Strike = ",$str1;
#	    printf "%-11s %5.2f\n","Slab Dip = ",$dip1;
#	    printf "%-17s %6.2f\n","Slab Thickness = ",$th1;
#	    printf "%-17s %6.2f\n","Slab Depth Unc = ",$dz1;
	    $nn++;
	}
    }
    $n++;
}
####
###
#####
sub round_to_nths {
    my ($num, $n) = @_;
    (int $num*$n)/$n
}
#####
