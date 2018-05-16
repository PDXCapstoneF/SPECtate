#! /bin/perl -w
use Cwd;

# -----------------------------------------------------------
# Start here
# -----------------------------------------------------------

# Read arguments and display them.
$NUM_ARG=$#ARGV +1;
if ($NUM_ARG != 1) {
	&usage();
}

print "$NUM_ARG \n";
print "$ARGV[0]\n";


# navigate to directory to be processed
$TOPDIR=$ARGV[0];
chdir $TOPDIR;
@TOPDIRARRAY = split('\ ', $TOPDIR);
$FileName=pop(@TOPDIRARRAY);
$OutPutFile=$FileName.".csv";

print"Output file name is $OutPutFile\n";


# Create list of directory to process.
@TEMPLIST = `dir`;

foreach (@TEMPLIST) {
	if ($_ =~ m/\d{6}/) {
      @LINE = split();
      push(@DIRLIST, $LINE[-1]);
	}
}

# @DIRLIST contains each of the directories to process.
# Create a file for output and print header info.
open (OUT, ">$OutPutFile")	
	or die "Cannot open the $OutPutFile: $!";
	
PrintHeaderLabels();

foreach (@DIRLIST) {
	print "********* working in $_ ************\n";
	chdir $_;
	$RunNum = $_;
	$FPoint=GetFailurePoint();
	
	# Get the information from the specjbb.props file 
	#GetPropsData();
	
	# Get the Max IR and Critical IR from the reporter.log file 
	GetIRData();
	
	
	
	# Process the GC data using Troys Script store output to Array to parse
	#GetGCData();
    
	
	#GetVMData();
	
	#Extract the JVM parameters from the ir.txt file.
	GetJVMParams();
	
	# Goto parent dir
	chdir "..";		
}
close OUT;



#------------------------------------------------------------
# Subroutines go here:
#   usage
#	GetPropsData
#  	GetIRData
#   GetJVMParams
# 	GetGCData
# 	GetVMData(Fpoint)
# -----------------------------------------------------------

#
# Get the Configuration data from the props file 
sub GetPropsData{
	print "\t*****Extracting configuration data************\n";
	if (open(IN, "<config\\specjbb2013.props")){
		while (<IN>) { 
			unless($_ !~ /^\s*$/){
				if($_ !~ m/^#/){
					print "MLQ $_";
				}
			}						
		} 
	}else{
		print "No configuration data found\n";
		return;
	}
	close IN;
}

# Process the vmstat data using by placing the entire log file into a arrays to parse
sub GetVMData{

	$Start=0;
	$End=0;
	
	print "\t*****Extracting VMstat data************\n";

	
	
	# Place the vmstat data into an Array
	@VMSTAT = ();
	
	if (open(IN, "<vmstat.log")){
		$row = 0;
		$column = 0;
				
		while (<IN>) { 
			if($_ =~ m/\s*\d\d +/){
				chomp;
				@line = split;
				foreach $column (@line){
					push @{$VMSTAT[$row]}, $column;
				}
				$row++;
			}
		} 
		
		# if VMSTAT data has not been processed yet.
		if(open (VMOUT, ">Vmstat.csv")){
			print "\t*****Print VMstat data out to file\n";
			# add the header to the vmstat.csv file
			@HeaderLine = ('HostName','TimeStamp','r','b','swpd','free','buff','cache','si','so','bi','bo','in','cs','us','sy','id','wa','st');
		
			foreach (@HeaderLine){
				print VMOUT "$_ ,";
			}
			print VMOUT "\n";
			foreach $row(@VMSTAT){
				foreach my $val(@$row){
					print VMOUT "$val ,";
				}
				print VMOUT"\n";
			}
		}			
		close VMOUT;
	}else{
		print "No VMstat data found\n";
		print OUT ", , , , ,";
		return;
	}
	close IN;
	
	$End=$FPoint-500;
	$Start=$FPoint-1100;
		
	$row = 0;
	$column = 0;
	$Interupt=0;
	$ContextSwitch=0;
	$UserCPU=0;
	$SystemCPU=0;
	
	# Calculate columns of data
	foreach $row ($Start..$End){
		$Interupt += $VMSTAT[$row][12];
		$ContextSwitch += $VMSTAT[$row][13];
		$UserCPU += $VMSTAT[$row][14];
		$SystemCPU += $VMSTAT[$row][15];
	}
	
	# divide to get Average
	$VMstatLength = 600;
	$Interupt /= $VMstatLength;
	$ContextSwitch /= $VMstatLength;
	$UserCPU /= $VMstatLength;
	$SystemCPU /= $VMstatLength;
	$TotalCPU = $UserCPU+$SystemCPU;

	print OUT "$Interupt, $ContextSwitch, $UserCPU, $SystemCPU, $TotalCPU,";
	
}

# Get the Max IR and Critical IR from the reporter.log file 
sub GetIRData{
	$MaxIR="";
	
	print "\t*****Extracting IR data************\n";
	
	my @files;
	opendir(DIR,".") or die "opening directory failed:$!";  # '.' for pwd.Use dir path if required. 
	while(my $filename=readdir(DIR)){
		push @files,$filename if($filename=~/.*.html$/);
	}

	if (open(IN, "<$files[0]")){
		while (<IN>) { 
			if($_ =~ m/^.*SPECjbb2015 Report.*/){
			 	@LINE = split();
				$MaxIR = "$LINE[-6]";
			}
			if($_ =~ m/^.*SPECjbb2015 Report.*/){
			 	@LINE = split();
				$CritIR = "$LINE[-3]";
			}
			if($_ =~ m/^.*settled.*\s(\d+).*$/){
				$HBIR = $1;
			}
			if($_ =~ m/^.*attempted.*\s(\d+).*$/){
				$ATTEMPT = $1;
			}
		} 
	}else{
		print "No IR data found\n";
		print OUT "\n $RunNum , ,";
		return;
	}
	print OUT " \n $RunNum, $MaxIR, $CritIR, $HBIR, $ATTEMPT,";
	close IN;
}

# Process the ir.txt file to extract JVM parameters
sub GetJVMParams {
	print "\t*****Extracting JVM parameters*****\n";
	
	open IN, "sut.txt" or die $!;
	while (<IN>) { 
		chomp();
		if($_ =~ /^All JVM options(.*$)/){
			print OUT "$1";
		}
		#unless($_ !~ /^Java Options for Backend:/){
	}
	close IN;
}


sub GetFailurePoint{
	print "\t*****Extracting Failurepoint************\n";
    open IN, "controller.out" or die $!;
	$line =0;
	
	
	while (<IN>) { 
		if(/\d+s: Failed, 4 overall retries left, retrying 1 of 1/){
			$line = <IN> ;
			#print $line;
			# 8766s: (97%)   IR = 186315 ..........?....|..............?...?....?.................?....?........ (rIR:aIR:PR = 186315:181365:180999) (tPR = 5748649) [OK] 
			if(/\s(\d+)s+.*/){
				print "\t******MLQ********first Failure Point is :$1 \n";
			}
						
			close IN;
			return $1;			
		}
	}
	close IN;
}

# Get GC data using a modified troys script.
sub GetGCData{
	$StartTime=1500;
	$EndTime=8000;
	$GC_Time=0;
    $Fpoint=0;
	
	open IN, "controller.out" or die $!;
	
	while (<IN>) { 
		if(/(\d+)s: Performing load levels/){
			#print "\t********Steady State started at $1\n";
			$StartTime=$1;
			$EndTime=$1+900;
		}
		elsif(/(\d+)s: Ramping up completed/){
			#print "\t********Steady State started at $1\n";
			$StartTime=$1;
			$EndTime=$1+900;
		}
		elsif(/(\d+)s: Building throughput-responsetime curve/){
			#print "\t********Steady State started at $1\n";
			$StartTime=$1;
			$EndTime=0;
			while(<IN>){
				if(/(\d+)s: max-jOPS is presumably .*/){
					#print "\t********Steady state ends at $1\n";
					$EndTime=$1;
				}
			}
			if($EndTime==0)
			{
				$EndTime=$StartTime+6000;
			}
		}		
		else
		{
			#print "\t********Looking at GC for non steady state work.\n";
		}
	}
	close IN;

	$GC_Time = $EndTime-$StartTime;
	$MyTime=$EndTime-600;
	print "\t********Steady State started at $StartTime\n";
	print "\t********Steady State ended at $EndTime\n";
	print "\t********Steady State lasted $GC_Time seconds\n";
	print OUT "$StartTime,$EndTime,$GC_Time";
  
	print "\t*****Extracting GC data************\n";
	print "\t*****Print GC Log data out to file\n";
	
	
	
	@GCDATA=`perl E:/PersonalDirectories/mljones2/2015Rollup/Rollup_ParseGC.pl -s $MyTime -e $EndTime Group1.Backend.JVM2.GC.log`;
	
	
	
	foreach(@GCDATA){
				print OUT "$_ ,";
			}
}

sub usage {
  print "\n";
  print "This script takes a directory of results from SPECjbb2012 and creates a table that summarizes results\n";
  print "\n";
  print "Usage: perl <Directory>\n";
  print "Invalid usage.\n";
  exit 0;
}

sub PrintHeaderLabels{
	print OUT "RunID "; 
	print OUT ",MaxIR ";
	print OUT ",CriIR ";
	print OUT ",HBIR Settled ";
	print OUT ",HBIR Attempted";
	print OUT ",GC Start Time";
	print OUT ",GC End Time";
	print OUT ",GC SS Period";
	print OUT ",Avg secs between Young GC";
	print OUT ",Avg secs between Full GC";
	print OUT ",Avg secs between ANY GC";
	print OUT ",Avg GC length(s) Young GC";
	print OUT ",Avg GC length(s) Full GC";
	print OUT ",Avg GC length(s) ANY GC";
	print OUT ",Time Spent(%) in Young GC";
	print OUT ",Time Spent(%) Full GC";
	print OUT ",Time Spent(%) ANY GC";
	print OUT ",Garbage Collected(K/s) Young";
	print OUT ",Garbage Collected(K/s) full";
	print OUT ",Garbage Collected(K/s) Total";
	print OUT ",Avg Resident Memory (K) Young";
	print OUT ",Avg Resident Memory (K) Old";
	print OUT ",Avg Resident Memory (K) Total";
	print OUT ",Avg Resident Memory (K) Perm ";
	print OUT ",Avg Resident Memory (K) Major";
	print OUT ",Interupts";
	print OUT ",ContextSwitch";
	print OUT ",UserCPU";
	print OUT ",SystemCPU";
	print OUT ",TotalCPU";
	print OUT ",Back End JVM Parameters";
}