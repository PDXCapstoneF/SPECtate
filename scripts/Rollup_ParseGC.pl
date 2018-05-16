#! /bin/perl -w
# -----------------------------------------------------------
# GC ROLLUP
# $Id: gcRollup.pl,v 1.04 2007/08/08 13:50:12 jburke Exp $
# 
# Copyright Intel Corporation (2007)
# This software is provided as is without any implied warranty.
#
# Performs a rollup of Garbage Collection data for a single file.
# -----------------------------------------------------------
use strict;

# ---------------------
# Initialize variables:
# ---------------------

my $gcOutBase = 'gcData';
my $saveFolder = '';
my $gcStartTime = undef;
my $gcEndTime = undef;
my $generationalGC = '0'; # by default, do not look for generational GC information

my $gcFormatFound = undef; #what type of GC format do we have?
my $gcCount = 0;
my $gcTime = 0;
my $resMem = 0;
my $gcIntervals = 0;
my $gcCollected = 0;
#my @allGcIntervals = ();

# For generational GC:
my $minorFormat = undef;
my $minorGcCount = 0;
my $minorGcTime = 0;
#my $minorResMem = 0;
my $minorGcIntervals = 0;
my $minorGcCollected = 0;
  
my $majorFormat = undef;
my $majorGcCount = 0;
my $majorGcTime = 0;
#my $majorResMem = 0;
my $majorGcIntervals = 0;
my $majorGcCollected = 0;
  
my $youngResMem = 0;
#my $youngAveResMem = 0;
my $oldResMem = 0;
#my $oldAveResMem = 0;
my $overallResMem = 0;
#my $overallAveResMem = 0;
my $permResMem = 0;
#my $permAveResMem = 0;
#my @allMinorGcIntervals;
#my @allMajorGcIntervals;

my $aftMajorGcResMem = 0;

my $verbose = '0'; # prints more outputs to the terminal, on by default

# All known GC Formats go here, as perl regular expressions
# NOTE -- We need to collect, in this order:
#   1. when the GC occured (in seconds since the AS started)
#   2. the amount of memory used by object BEFORE the GC event 
#   3. the amount of memory used by object AFTER the GC event (the resident memory)
#   4. the length of the GC event
#   5. the units of length (sec and ms are currently supported)

my(@gcFormats) = (
  
  # ariane # [memory ] 1389.600-1390.280: GC 6291456K->1638763K (6291456K), 679.662 ms
  '^\[memory \] (\d+\.\d+)-\d+\.\d+: GC \d+K->(\d+)K \(\d+K\), (\d+\.\d+) (ms)',
   
  # viking # [10740][memory ] 918.261: GC 1572864K->394517K (1572864K) in 452.723 ms
  '^\[\d+\]\[memory \] (\d+\.\d+): GC \d+K->(\d+)K \(\d+K\) in (\d+\.\d+) (ms)',
  '^\[\s+\d+\]\[memory \] (\d+\.\d+): GC \d+K->(\d+)K \(\d+K\) in (\d+\.\d+) (ms)'
  ,          
  # R27.1  # [memory ][INFO ] 1199.167-1199.869: GC 14336000K->1186518K (14336000K), 702.495 ms
  '^\[memory \]\[INFO \] (\d+\.\d+)-\d+\.\d+: GC \d+K->(\d+)K \(\d+K\), (\d+\.\d+) (ms)',
 
  # R27.2  # [INFO ][memory ] 1199.167-1199.869: GC 14336000K->1186518K (14336000K), 702.495 ms  
  '^\[INFO \]\[memory \] (\d+\.\d+)-\d+\.\d+: GC (\d+)K->(\d+)K \(\d+K\), (\d+\.\d+) (ms)',
  
  # Oracle data/non-generational Sun # 24.362: [GC 571392K->63488K(2659328K), 0.2451460 secs]
#  '^(\d+\.\d+): \[GC (\d+)K\-\>(\d+)K\(\d+K\), (\d+\.\d+) (secs)\]',

#  [INFO ][memory ] 191.937-192.682: GC 1063966K->1478956K (2478080K), sum of pauses 374.267 ms
  '^\[INFO \]\[memory \] (\d+\.\d+)-\d+\.\d+: GC (\d+)K->(\d+)K \(\d+K\), sum of pauses (\d+\.\d+) (ms)',
  ); 

# For minor generational GC events (not full GC's):
# NOTE: -- We need to collect, in this order:
#   1. when the GC occured
#   2. amount of "young" memory after the event
#   3. amount of "overall" memory before the event
#   4. amount of "overall" memory after the event
#   5. length of the event
#   6. units of the length (secs or ms)
my(@minorGcFormats) = (
 # HotSpot jdk8 build 104
 #1716.297: [GC (Allocation Failure) [PSYoungGen: 87700282K->1018666K(92100096K)] 87919406K->1237791K(95245824K), 0.1257350 secs] [Times: user=3.65 sys=0.00, real=0.13 secs] 
  '^(\d+\.\d+): \[GC \(Allocation Failure\) \[PSYoungGen: \d+K->(\d+)K\(\d+K\)\] (\d+)K->(\d+)K\(\d+K\), (\d+\.\d+) (secs)\].*$', 

 #Hotspot JDK8 with ParallelRefProcEnable
  #4476.249: [GC (Allocation Failure) 4476.890: [SoftReference, 0 refs, 0.0023880 secs]4476.892: [WeakReference, 206178 refs, 0.0055110 secs]4476.898: [FinalReference, 35156 refs, 0.0178740 secs]4476.916: [PhantomReference, 0 refs, 0.0012550 secs]4476.917: [JNI Weak Reference, 0.0000020 secs][PSYoungGen: 15952384K->1296384K(16088896K)] 48852317K->35229981K(51042112K), 0.6798190 secs] [Times: user=10.57 sys=0.02, real=0.68 secs] 
  '^(\d+\.\d+): \[GC \([^)]*\) \d+\.\d+: \[SoftRef[^]]*\]\d+\.\d+: \[WeakRef[^]]*\]\d+\.\d+: \[FinalRef[^]]*\]\d+\.\d+: \[PhantomRef[^]]*\]\d+\.\d+: \[JNI[^]]*\]\[PSYoungGen: \d+K->(\d+)K\(\d+K\)\] (\d+)K->(\d+)K\(\d+K\), (\d+\.\d+) (secs)\].*$', 

  #Hospot JDK8
  #3657.430: [GC (GCLocker Initiated GC) [PSYoungGen: 15368000K->1839104K(15494912K)] 48878080K->36325709K(50448128K), 0.8263800 secs] [Times: user=10.74 sys=0.01, real=0.82 secs] 
 ## '^(\d+\.\d+): \[GC \([^)]*\) \[PSYoungGen: \d+K->(\d+)K\(\d+K\)\] (\d+)K->(\d+)K\(\d+K\), (\d+\.\d+) (secs)\].*$', 
  
  # Adaptive Sizing # 0.357: [GC Desired survivor size 2952790016 bytes, new threshold 7 (max 15) [PSYoungGen: 17301504K->3166K(20185088K)] 17301504K->3174K(24379392K), 0.0124650 secs] [Times: user=0.11 sys=0.01, real=0.01 secs] 
  '^(\d+\.\d+): \[GC Desired.* \[PSYoungGen: \d+K->(\d+)K\(\d+K\)\] \d+K->(\d+)K\(\d+K\), (\d+\.\d+) (secs)\]',

  # Sun JVM # 3628.003: [GC [PSYoungGen: 2430464K->59392K(2472128K)] 5387657K->3018515K(5433536K), 0.0809070 secs]
  '^(\d+\.\d+): \[GC \[PSYoungGen: \d+K->(\d+)K\(\d+K\)\] \d+K->(\d+)K\(\d+K\), (\d+\.\d+) (secs)\]',

  #[INFO ][memory ] 37.537: parallel nursery GC 812460K->350834K (1048576K), 56.679 ms
#  '^\[INFO \]\[memory \] (\d+\.\d+): parallel nursery GC ()(\d+)K->(\d+)K \(\d+K\), (\d+\.\d+) (ms)',

  # hotspot 1.6.0_16 
  #396.509: [GC 3224680K->329724K(12058624K), 0.1669350 secs] 
#  '^(\d+\.\d+): \[GC ()(\d+)K->(\d+)K\(\d+K\), (\d+\.\d+) (secs)\]',

  # hotspot 1.6.0_23 and JDK7 with +XX:+PrintGCDetails:
  # 716.808: [GC [PSYoungGen: 88092060K->1347526K(92099968K)] 88281859K->1537325K(95245696K), 0.1577260 secs] [Times: user=4.64 sys=0.01, real=0.16 secs]   
  #1169.101: [GC [PSYoungGen: 4544256K->401408K(4680512K)] 12678956K->8848492K(13331264K), 0.5293150 secs] [Times: user=4.49 sys=0.13, real=0.53 secs] 
  '^(\d+\.\d+): \[GC \[PSYoungGen: \d+K->(\d+)K\(\d+K\)\] (\d+)K->(\d+)K\(\d+K\), (\d+\.\d+) (secs)\].*$',
  
  # hotspot <-XX:+UseParNewGC> 
  #34.232: [GC 34.232: [ParNew: 18820878K->591879K(20761856K), 0.1503520 secs] 18821539K->592540K(22859008K), 0.1504040 secs] [Times: user=2.29 sys=0.07, real=0.15 secs]
#  '^(\d+\.\d+): \[GC \d+\.\d+: \[ParNew: \d+K->(\d+)K\(\d+K\), \d+\.\d+ secs\] (\d+)K->(\d+)K\(\d+K\), (\d+\.\d+) (secs)\].*$',

  #JRockit R28: [INFO ][memory ] [YC#6] 220.280-220.386: YC 3447103KB->3461120KB (3461120KB), 0.106 s, sum of pauses 105.182 ms, longest pause 105.182 ms.
#  '^\[INFO \]\[memory \] \[YC#\d+\] (\d+\.\d+)-\d+\.\d+: YC ()(\d+)KB->(\d+)KB \(\d+KB\), \d+\.\d+ s, sum of pauses (\d+\.\d+) (ms), longest pause \d+\.\d+ ms\.',

  #JRockit R28 verbose with info/timstamp: [INFO ][memory ][Tue Dec  7 15:31:06 2010][1291764666219][23283] [YC#129] 110.622-110.623: YC 35004KB->10430KB (65536KB), 0.001 s, sum of pauses 1.164 ms, longest pause 1.164 ms.
#  '^\[INFO \]\[memory \]\[[^]]+\]\[\d+\]\[\d+\] \[YC#\d+\] (\d+\.\d+)-\d+\.\d+: YC ()(\d+)KB->(\d+)KB \(\d+KB\), \d+\.\d+ s, sum of pauses (\d+\.\d+) (ms), longest pause \d+\.\d+ ms\.',

  );

# For major generational GC events (full GC's):
# NOTE: -- We need to collect, in this order:
#   1. when the GC occured
#   2. amount of "young" memory after the event
#   3. amount of "old" memory after the event
#   4. amount of "overall" memory before the event
#   5. amount of "overall" memory after the event
#   6. amount of "permanent" memory after the event
#   7. length of the event
#   8. units of the length (secs or ms)
my(@majorGcFormats) = ( 

# HotSpot JDK8 build 104
#137.315: [Full GC (System.gc()) [PSYoungGen: 18285K->0K(92100096K)] [ParOldGen: 134K->17132K(3145728K)] 18420K->17132K(95245824K), [Metaspace: 16045K->16045K(118784K)], 0.0419840 secs] [Times: user=0.23 sys=0.04, real=0.04 secs] 
  '^(\d+\.\d+): \[Full GC \(System.gc\(\)\) \[PSYoungGen: \d+K->(\d+)K\(\d+K\)\] \[ParOldGen: \d+K->(\d+)K\(\d+K\)\] (\d+)K->(\d+)K\(\d+K\), \[Metaspace: \d+K->(\d+)K\(\d+K\)\], (\d+\.\d+) (secs)\].*',
 
 #Hotspot JDK8 with ParallelRefProcEnable
  #4476.935: [Full GC (Ergonomics) 4483.457: [SoftReference, 0 refs, 0.0025710 secs]4483.459: [WeakReference, 630638 refs, 0.0228800 secs]4483.482: [FinalReference, 154037 refs, 0.0212240 secs]4483.504: [PhantomReference, 13 refs, 0.0013980 secs]4483.505: [JNI Weak Reference, 0.0000020 secs][PSYoungGen: 1296384K->0K(16088896K)] [ParOldGen: 33933597K->9817277K(34953216K)] 35229981K->9817277K(51042112K), [Metaspace: 212975K->212975K(224754K/323584K)], 10.7266200 secs] [Times: user=154.17 sys=0.63, real=10.72 secs] 
  '^(\d+\.\d+): \[Full GC \([^)]*\) \d+\.\d+: \[SoftRef[^]]*\]\d+\.\d+: \[WeakRef[^]]*\]\d+\.\d+: \[FinalRef[^]]*\]\d+\.\d+: \[PhantomRef[^]]*\]\d+\.\d+: \[JNI[^]]*\]\[PSYoungGen: \d+K->(\d+)K\(\d+K\)\] \[ParOldGen: \d+K->(\d+)K\(\d+K\)\] (\d+)K->(\d+)K\(\d+K\), \[Metaspace: \d+K->(\d+)K\(\d+K\/\d+K\)\], (\d+\.\d+) (secs)\].*',  
  
  #Hospot JDK8
  #3658.266: [Full GC (Ergonomics) [PSYoungGen: 1839104K->0K(15494912K)] [ParOldGen: 34486605K->9522772K(34953216K)] 36325709K->9522772K(50448128K), [Metaspace: 226228K->226228K(241442K/333824K)], 10.1435060 secs] [Times: user=136.97 sys=0.22, real=10.14 secs] 
  #1169.631: [Full GC [PSYoungGen: 401408K->0K(4680512K)] [ParOldGen: 8447084K->2251302K(8650752K)] 8848492K->2251302K(13331264K) [PSPermGen: 272585K->268878K(524288K)], 7.0569350 secs] [Times: user=77.43 sys=0.13, real=7.05 secs]
  '^(\d+\.\d+): \[Full GC \([^)]*\) \[PSYoungGen: \d+K->(\d+)K\(\d+K\)\] \[ParOldGen: \d+K->(\d+)K\(\d+K\)\] (\d+)K->(\d+)K\(\d+K\), \[Metaspace: \d+K->(\d+)K\(\d+K\/\d+K\)\], (\d+\.\d+) (secs)\].*',
   
 #404.834: [Full GC (System) [PSYoungGen: 182342K->0K(20185088K)] [ParOldGen: 95223K->188509K(4194304K)] 277565K->188509K(24379392K) [PSPermGen: 18906K->18906K(36864K)], 0.0745350 secs] [Times: user=0.36 sys=0.12, real=0.07 secs] 
   '^(\d+\.\d+): \[Full GC \(System\) \[PSYoungGen: \d+K->(\d+)K\(\d+K\)\] \[ParOldGen: \d+K->(\d+)K\(\d+K\)\] (\d+)K->(\d+)K\(\d+K\) \[PSPermGen: \d+K->(\d+)K\(\d+K\)\], (\d+\.\d+) (secs)\].*',

  # Sun JVM # 3628.084: [Full GC [PSYoungGen: 59392K->0K(2472128K)] [PSOldGen: 2959123K->765191K(2797568K)] 3018515K->765191K(5269696K) [PSPermGen: 66074K->66074K(131072K)], 2.3901990 secs]
  #'(\d+\.\d+): \[Full GC \[PSYoungGen: \d+K->(\d+)K\(\d+K\)\] \[PSOldGen: \d+K->(\d+)K\(\d+K\)\] \d+K->(\d+)K\(\d+K\) \[PSPermGen: \d+K->(\d+)K\(\d+K\)\], (\d+\.\d+) (secs)\]',
  '(\d+\.\d+): \[Full GC \[PSYoungGen: \d+K->(\d+)K\(\d+K\)\] \[ParOldGen: \d+K->(\d+)K\(\d+K\)\] \d+K->(\d+)K\(\d+K\) \[PSPermGen: \d+K->(\d+)K\(\d+K\)\], (\d+\.\d+) (secs)\]',
 
  # R27.2  # [INFO ][memory ] 1199.167-1199.869: GC 14336000K->1186518K (14336000K), 702.495 ms  
  '^\[INFO \]\[memory \] (\d+\.\d+)-\d+\.\d+: GC ()()(\d+)K->(\d+)K \(\d+K\), ()(\d+\.\d+) (ms)',
  
#  [INFO ][memory ] 191.937-192.682: GC 1063966K->1478956K (2478080K), sum of pauses 374.267 ms
  '^\[INFO \]\[memory \] (\d+\.\d+)-\d+\.\d+: GC ()()(\d+)K->(\d+)K \(\d+K\), ()sum of pauses (\d+\.\d+) (ms)',

  # hotspot 1.6.0_16 
  #1203.879: [Full GC 8484840K->4378149K(12014592K), 7.3594280 secs]
  '^(\d+\.\d+): \[Full GC ()()(\d+)K->(\d+)K\(\d+K\), ()(\d+\.\d+) (secs)\]',

  # hotspot 1.6.0_23 with +XX:+PrintGCDetails:
  #1169.631: [Full GC [PSYoungGen: 401408K->0K(4680512K)] [ParOldGen: 8447084K->2251302K(8650752K)] 8848492K->2251302K(13331264K) [PSPermGen: 272585K->268878K(524288K)], 7.0569350 secs] [Times: user=77.43 sys=0.13, real=7.05 secs]
  '^(\d+\.\d+): \[Full GC \[PSYoungGen: \d+K->(\d+)K\(\d+K\)\] \[ParOldGen: \d+K->(\d+)K\(\d+K\)\] (\d+)K->(\d+)K\(\d+K\) \[PSPermGen: \d+K->(\d+)K\(\d+K\)\], (\d+\.\d+) (secs)\].*',

  #JRockit R28: [INFO ][memory ] [OC#1] 220.386-221.088: OC 3461120KB->711922KB (3461120KB), 0.702 s, sum of pauses 568.586 ms, longest pause 568.586 ms.
  '^\[INFO \]\[memory \] \[OC#\d+\] (\d+\.\d+)-\d+\.\d+: OC ()()(\d+)KB->(\d+)KB \(\d+KB\), \d+\.\d+ s, ()sum of pauses (\d+\.\d+) (ms), longest pause \d+\.\d+ ms\.',
  
    #JRockit R28 verbose with info/timstamp: [INFO ][memory ][Sun Dec  5 04:03:26 2010][1291550606514][04017] [OC#147] 9147.180-9154.377: OC 24577890KB->21578134KB (25165824KB), 7.197 s, sum of pauses 6919.665 ms, longest pause 6919.665 ms.
  '^\[INFO \]\[memory \]\[[^]]+\]\[\d+\]\[\d+\] \[OC#\d+\] (\d+\.\d+)-\d+\.\d+: OC ()()(\d+)KB->(\d+)KB \(\d+KB\), \d+\.\d+ s, ()sum of pauses (\d+\.\d+) (ms), longest pause \d+\.\d+ ms\.',

  );

# -------------
# Start Here:
# -------------

# Read arguments
if ($#ARGV == -1) {
  &usage();
}

my $i;
for( $i = 0; $i <= $#ARGV; $i ++)
    {
    my $each = $ARGV[$i];
    last unless $each =~ /^-.*/;
  
  # Note: use ++ $i to ensure $i is incrimented BEFORE being used as an index
    if ($each eq "-s" || $each eq "-start") {
      $gcStartTime = $ARGV[++$i];
      next;
        }
    elsif ($each eq "-e" || $each eq "-end") {
        $gcEndTime = $ARGV[++$i];
        next;
        }
    elsif ($each eq "-b" || $each eq "-base") {
        $gcOutBase = $ARGV[++$i];
        next;
        }
    elsif ($each eq '-d' || $each eq "-destination") {
        $saveFolder = $ARGV[++$i];
        next;
        }
    elsif ($each eq "-help" || $each eq "-h" || $each eq "/?") {
        &usage();
        }
    else  # catch-all for errors
        {
        print "Unknown option $each\n";
        exit 1;
        }
    } # end switches loop
  
# Read the file name
if ($i > $#ARGV) {
  print "No File specified\n";
  &usage();
    }

my $gcFileName = $ARGV[$i++];

unless( defined($gcFileName) )
    {
    print "No file specified!\n";
    exit 1;
    }

$gcOutBase = $gcFileName;
$gcOutBase =~ s/gclogjr-FOD0.out/gc-FOD0/;
$gcOutBase =~ s/gclogjr-FOD1.out/gc-FOD1/;
$gcOutBase =~ s/gclogjr.out/gc/;
$gcOutBase =~ s/gclog.out/gc/;

# Read the optional save location for the output file
#if ($i <= $#ARGV) {
#  $saveFolder = $ARGV[$i++];
#}

# Read the optional name base for the output file
#if ($i <= $#ARGV) {
#  $gcOutBase = $ARGV[$i++];
#}

# -----------------------------------------------------------
# Read the gc file
# -----------------------------------------------------------
print "Reading GC data...\n" if $verbose;

die "$gcFileName does not exsist!\n" unless (-f "$gcFileName");

if ( !open(IN, "<$gcFileName")) {
  print "Error reading $gcFileName: $!\n";
  exit 1; 
}

my $line;
my $lastGcTime = 0;
my $lastMinorGcTime = 0;
my $lastMajorGcTime =  0;

#####################MLQ
if(open (GC_OUT, ">GC_log.csv")){
	#print GC_OUT   "Type, StartTime, youngMem, overallBefore, overallMem, len, oldMem, permMem\n";
	print GC_OUT   "Type, StartTime, SurvivorSize, UsedMemYGandOG, ResMemOGandSurvior, len\n";
	}

while( $line = <IN> )
    {
    $line = &chompLine($line);  # trim EOL chars    

#---------------------
# Look for a GC format
#---------------------

    if( !defined $gcFormatFound && !$generationalGC )
        {
        for( my $j=0; $j<=$#gcFormats; $j++ )
            {
            $gcFormatFound = $gcFormats[$j] if ($line =~ m/$gcFormats[$j]/  );
            }
        } # done looking for a format match

    if( !defined $gcFormatFound && !defined $minorFormat )  # look for a minor GC format match
        {
        for( my $j=0; $j<=$#minorGcFormats; $j++ )
            {
            if( $line =~ m/$minorGcFormats[$j]/ )
                {
                $minorFormat = $minorGcFormats[$j];
#                $majorFormat = $majorGcFormats[$j];
                $generationalGC = 1;
                print "Generational GC data found!\n" if $verbose;
                }
            }
        } # done looking for a minor GC format match

    if( !defined $gcFormatFound && !defined $majorFormat )  # look for a Full/Major GC format match
        {
        for( my $j=0; $j<=$#majorGcFormats; $j++ )
            {
            if ($line =~ m/$majorGcFormats[$j]/  )
                {
                $majorFormat = $majorGcFormats[$j];
#                $minorFormat = $minorGcFormats[$j];
                $generationalGC = 1;
                print "Generational GC data found!\n" if $verbose;
                }
            }
        } # done looking for a major GC format match

#------------------------------------
# Generational GC data 
#------------------------------------    

    if( $generationalGC )  # if we have generational GC data:
        {
            
#------------------
# Collect the GC's:
#------------------

        if (defined $minorFormat
         && $line =~ m/$minorFormat/  )
           {
            my(
               $when,            #   1. when the GC occured
               $youngMem,        #   2. amount of "young" memory after the event
                $overallBefore,   #   3. amount of overall memory before the event
                $overallMem,      #   4. amount of "overall" memory after the event
                $len,             #   5. length of the event
                $units            #   6. units of the length (secs or ms)
                ) = ($1, $2, $3, $4, $5, $6);
				
#check if we're in steady state or have null values
            next if( defined $gcStartTime && $when < $gcStartTime );
            next if( defined $gcEndTime   && $when > $gcEndTime );

            $len = $len / 1000.0 if $units eq 'ms'; # convert to seconds if in ms
            $minorGcCount++;  #count the minor GC
            $gcCount++;  #count the GC

            if ($lastMinorGcTime != 0)   # if this isn't the first minor GC
                {
                my $currentMinorGcInterval = ($when - $lastMinorGcTime);
                $minorGcIntervals += $currentMinorGcInterval;              
#               $allMinorGcIntervals[$#allMinorGcIntervals+1] = $currentMinorGcInterval; # add the current interval to the list of all minor intervals
               }
           $lastMinorGcTime = $when + $len; # Account for time in GC, $when is the START time for a GC event

            if ($lastGcTime != 0)   # if this isn't the first GC
               {
                my $currentGcInterval = ($when - $lastGcTime);
                $gcIntervals += $currentGcInterval;              
#               $allGcIntervals[$#allGcIntervals+1] = $currentGcInterval; # add the current interval to the list of all intervals
                }
            $lastGcTime = $when + $len; # Account for time in GC, $when is the START time for a GC event

            $minorGcTime += $len;
            $youngResMem += $youngMem       if( $youngMem ne "" );
            $overallResMem += $overallMem;
            $minorGcCollected += ($overallBefore-$overallMem);

			#####################MLQ
    		print GC_OUT  "Young, ".$when .",".$youngMem.",". $overallBefore.",".$overallMem.",".$len."\n";
			
           }
        elsif( defined $majorFormat
         && $line =~ /$majorFormat/ )
            {
            my(
              $when,            #   1. when the GC occured
              $youngMem,        #   2. amount of "young" memory after the event
              $oldMem,          #   3. amount of "old" memory after the event
              $overallBefore,   #   4. amount of overall memory before the event
              $overallMem,      #   5. amount of "overall" memory after the event
              $permMem,         #   6. amount of "permanent" memory after the event
              $len,             #   7. length of the event
              $units            #   8. units of the length (secs or ms)
              ) = ( $1, $2, $3, $4, $5, $6, $7, $8);
          
#check if we're in steady state or have null values
            next if( defined $gcStartTime && $when < $gcStartTime );
            next if( defined $gcEndTime   && $when > $gcEndTime );

            $len = $len / 1000.0 if $units eq 'ms'; # convert to seconds if in ms

            $aftMajorGcResMem += $overallMem;
            $majorGcCount++;  #count the major GC
            $gcCount++;  #count the GC

            if ($lastMajorGcTime != 0)   # if this isn't the first major GC
                {
                my $currentMajorGcInterval = ($when - $lastMajorGcTime);
                $majorGcIntervals += $currentMajorGcInterval;              
#               $allMajorGcIntervals[$#allMajorGcIntervals+1] = $currentMajorGcInterval; # add the current interval to the list of all major intervals
                }
            $lastMajorGcTime = $when + $len; # Account for time in GC, $when is the START time for a GC event

            if ($lastGcTime != 0)   # if this isn't the first GC
                {
                my $currentGcInterval = ($when - $lastGcTime);
                $gcIntervals += $currentGcInterval;              
#               $allGcIntervals[$#allGcIntervals+1] = $currentGcInterval; # add the current interval to the list of all intervals
                }
            $lastGcTime = $when + $len; # Account for time in GC, $when is the START time for a GC event

            $majorGcTime += $len;
            $youngResMem += $youngMem       if( $youngMem ne "" );
            $oldResMem += $oldMem           if( $oldMem ne "" );
            $overallResMem += $overallMem;
            $permResMem += $permMem         if( $permMem ne "" );
            $majorGcCollected += ($overallBefore-$overallMem);

			#####################MLQ
    		print GC_OUT  "FULL,".$when .",".$youngMem.",". $overallBefore.",".$overallMem.",".$len.",".$oldMem.",".$permMem."\n";
			                 
#die "Negative GC collection: $line \n" if( $overallBefore-$overallMem < 0 );

#           $allMajorGcTime[$#allMajorGcTime+1] = $len; # add the last GC to the list of all GC's          
#           $allYoungResMem[$#allYoungResMem+1] = $youngMem; # add the last memory amount to the list of all memory amounts
#           $allOldResMem[$#allOldResMem+1] = $oldMem; # add the last memory amount to the list of all memory amounts
#           $allOverallResMem[$#allOverallResMem+1] = $overallMem; # add the last memory amount to the list of all memory amounts
#           $allPermResMem[$#allPermResMem+1] = $permMem; # add the last memory amount to the list of all memory amounts
            } # end format check
        else
            {
            # print "Ignored: $line \n"
            }
        } # end generational GC check

#------------------------------------
# Normal GC data (non-generational)
#------------------------------------    

    else                # we have standard GC data:
        {
        
    #------------------
    # Collect the GC's:
    #------------------
    
        if( $gcFormatFound
         && $line =~ m/$gcFormatFound/ )   #check that we've found a GC format, then check if the line matches our format
            {
            my (
                $when,              # 1. When the GC occured (secs after jvm launch)
                $overallBefore,     # 2. amount of overall memory before the event
                $mem,               # 3. The amount of memory held by objects AFTER the GC event 
                $len,               # 4. Length of the GC event (total pause)
                $units              # 5. units for the length of the GC (sec or ms)
                ) = ($1, $2, $3, $4, $5);

#check if we're in steady state or have null values
            next if( defined $gcStartTime && $when < $gcStartTime );
            next if( defined $gcEndTime   && $when > $gcEndTime );

            $len = $len / 1000.0 if $units eq 'ms'; # convert to seconds if in ms

            $gcCount++;  #count the GC

            if ($lastGcTime != 0)   # if this isn't the first GC
                {
                my $currentGcInterval = ($when - $lastGcTime);
                $gcIntervals += $currentGcInterval;              
#              $allGcIntervals[$#allGcIntervals+1] = $currentGcInterval; # add the current interval to the list of all intervals
               }
           $lastGcTime = $when + $len; # Account for time in GC, $when is the START time for a GC event

            $gcTime += $len;
            $resMem += $mem;
            $gcCollected += ($overallBefore-$mem);

#die "Negative GC collection: $line \n" if( $overallBefore-$mem < 0 );

#           $allGcTime[$#allGcTime+1] = $len; # add the last GC to the list of all GC's          
#           $allResMem[$#allResMem+1] = $mem; # add the last memory amount to the list of all memory amounts
            } # end match if
        else
            {
            #print "Ignored: $line \n"
            }
        }
    } # end while loop

	close GC_OUT;
	
# exit if no GC data found in file
die "No GC data" if $gcCount == 0 && $majorGcCount == 0 && $minorGcCount == 0;

# -----------------------------------------------------------
# Open the output file
# -----------------------------------------------------------
my $gcOutName = "$gcOutBase-summary.out";
#$gcOutName = "$saveFolder/$gcOutBase-summary.tsv" if ($saveFolder ne "");
print "Creating $gcOutName...\n" if $verbose;

#if (-f $gcOutName) {
#  print "Moving existing file to .old...\n" if $verbose;
#  unlink("$gcOutName.old");
#  rename($gcOutName, "$gcOutName.old")
#    || die "Unable to rename $gcOutName to $gcOutName.old: $!\n";
#}
print "Saving $gcOutName...\n" if $verbose;

open(OUT, ">$gcOutName") || die "Error writing $gcOutName: $!";

# -----------------
# Print the headings and data:
# -----------------

#print OUT '#Id: gcRollup.pl,v 1.04 2007/08/08 13:50:12 jburke ';

my $gcDuration = $lastGcTime;
$gcDuration = $lastMinorGcTime if( $lastMinorGcTime > $gcDuration );
$gcDuration = $lastMajorGcTime if( $lastMajorGcTime > $gcDuration );
$gcDuration = $gcEndTime       if( defined $gcEndTime && $gcEndTime < $gcDuration );
$gcDuration = $gcDuration - $gcStartTime if( defined $gcStartTime );

print OUT "\n\"GC File Analyzed:\" \t $gcFileName";
print OUT "\n\"GC Start Time:\"    \t $gcStartTime" if( defined $gcStartTime );
print OUT "\n\"GC Stop Time:\"     \t $gcEndTime"   if( defined $gcEndTime );
print OUT "\n\"GC Duration (s):\"  \t $gcDuration";
#print OUT "\n ";

# ---------------------
# Compute GC statistics
# ---------------------

if( !$generationalGC )
    { 
    my $gcRate = $gcIntervals / ($gcCount - 1);
    my $gcAverage = $gcTime / $gcCount;
    my $aveResMem = $resMem / $gcCount;

    print OUT "\n\"Avg secs between GC\"    ";
    print OUT "\t" . $gcRate ;
    print OUT "\n\"Avg GC length (s)\"      ";
    print OUT "\t" . $gcAverage ;
    print OUT "\n\"Time Spent in GC (%)\"   ";
    print OUT "\t" . (100*$gcTime/$gcDuration) ;
    print OUT "\n\"Garbage Collect (K/s)\"  ";
    print OUT "\t" . int($gcCollected/$gcDuration) ;
    print OUT "\n\"Avg Resident Memory (K)\"";
    print OUT "\t" . int $aveResMem ;

  # ---------------------------------------------------------------------
  # For trends, we need to perform some calculations:
  # Each trend is the percent ERROR between the average of the last 
  #   <sampleSize> values and the average of the 1st <sampleSize> values.
  # ---------------------------------------------------------------------
    #my $sampleSize = 3;
    #my $tmpStartAverage = getAverage(0, $sampleSize-1, @allGcIntervals);
    #my $tmpEndAverage = getAverage($#allGcIntervals-$sampleSize+1, $#allGcIntervals, @allGcIntervals);
    #my $tmpTrend = 0.0; 
    #print OUT "\n trendGcIntervals";
    #if (($tmpStartAverage eq "NA") || ($tmpEndAverage eq "NA"))
    #    {
    #    print OUT "\tNA";
    #    }
    #else
    #    {
    #    $tmpTrend = 100.0 * ($tmpEndAverage - $tmpStartAverage) / $tmpStartAverage;
    #    print OUT "\t\t\t$tmpTrend\%";
    #    }
    #
    #$tmpStartAverage = getAverage(0, $sampleSize-1, @allGcTime);
    #$tmpEndAverage = getAverage($#allGcTime-$sampleSize+1, $#allGcTime, @allGcTime);
    #print OUT "\n trendGcTime";
    #if (($tmpStartAverage eq "NA") || ($tmpEndAverage eq "NA"))
    #    {
    #    print OUT "\tNA";
    #    }
    #else
    #    {
    #    $tmpTrend = 100.0 * ($tmpEndAverage - $tmpStartAverage) / $tmpStartAverage;
    #    print OUT "\t\t\t$tmpTrend\%";
    #    }
    #
    #$tmpStartAverage = getAverage(0, $sampleSize-1, @allResMem);
    #$tmpEndAverage = getAverage($#allResMem-$sampleSize+1, $#allResMem, @allResMem);
    #print OUT "\n trendResMem";
    #if (($tmpStartAverage eq "NA") || ($tmpEndAverage eq "NA"))
    #    {
    #    print OUT "\tNA";
    #    }
    #else
    #    {
    #    $tmpTrend = 100.0 * ($tmpEndAverage - $tmpStartAverage) / $tmpStartAverage;
    #    print OUT "\t\t\t$tmpTrend\%";
    #    }
    }
else  #if we have generational GC...
    {
    if ($minorGcCount <= 1) {
            $minorGcCount = 2;
        }
    if ($majorGcCount <= 1) {
            $majorGcCount = 2;
        }
    my $minorGcRate     = $minorGcIntervals / ($minorGcCount - 1);
    my $minorGcAverage  = $minorGcTime / $minorGcCount;
    my $majorGcRate     = $majorGcIntervals / ($majorGcCount - 1);
    my $majorGcAverage  = $majorGcTime / $majorGcCount;
    my $aveYoungResMem  = $youngResMem / ($minorGcCount + $majorGcCount);  # youngMem done every time
    my $aveOldResMem    = $oldResMem / $majorGcCount; # old only done at full GC's
    my $aveOverallResMem= $overallResMem / ($minorGcCount + $majorGcCount); # overallMem done every time
    my $avePermResMem   = $permResMem / $majorGcCount; # perm only done at full GC's

    print "," . $minorGcRate ;
    print "," . $majorGcRate ;
    print "," . ( $gcIntervals / ($gcCount - 1) );
    print "," . $minorGcAverage ;
    print "," . $majorGcAverage ;
    print "," . ( $majorGcTime + $minorGcTime ) / ($majorGcCount + $minorGcCount);
    print "," . (100*$minorGcTime/$gcDuration) ;
    print "," . (100*$majorGcTime/$gcDuration) ;
    print "," . (100*($minorGcTime+$majorGcTime)/$gcDuration) ;
    print "," . int($minorGcCollected/$gcDuration) ;
    print "," . int($majorGcCollected/$gcDuration) ;
    print "," . int(($majorGcCollected+$minorGcCollected)/$gcDuration) ;
    print "," . int $aveYoungResMem ;
    print "," . int $aveOldResMem ;
    print "," . int $aveOverallResMem ;
    print "," . int $avePermResMem ;
    print "," . int ($aftMajorGcResMem / $majorGcCount) ;


    # print "\n\"Avg secs between GC partial\"  ";
    # print "\t" . $minorGcRate ;
    # print "\n\"Avg secs between GC full\"     ";
    # print "\t" . $majorGcRate ;
    # print "\n\"Avg secs between GC (any)\"    ";
    # print "\t" . ( $gcIntervals / ($gcCount - 1) );
    # print "\n\"Avg GC length (s) partial\"    ";
    # print "\t" . $minorGcAverage ;
    # print "\n\"Avg GC length (s) full\"       ";
    # print "\t" . $majorGcAverage ;
    # print "\n\"Avg GC length (s) total\"      ";
    # print "\t" . ( $majorGcTime + $minorGcTime ) / ($majorGcCount + $minorGcCount);
    # print "\n\"Time Spent in GC (%) partial\" ";
    # print "\t" . (100*$minorGcTime/$gcDuration) ;
    # print "\n\"Time Spent in GC (%) full\"    ";
    # print "\t" . (100*$majorGcTime/$gcDuration) ;
    # print "\n\"Time Spent in GC (%) total\"   ";
    # print "\t" . (100*($minorGcTime+$majorGcTime)/$gcDuration) ;
    # print "\n\"Garbage Collect (K/s) partial\"";
    # print "\t" . int($minorGcCollected/$gcDuration) ;
    # print "\n\"Garbage Collect (K/s) full\"   ";
    # print "\t" . int($majorGcCollected/$gcDuration) ;
    # print "\n\"Garbage Collect (K/s) total\"  ";
    # print "\t" . int(($majorGcCollected+$minorGcCollected)/$gcDuration) ;
    # print "\n\"Avg Resident Memory (K) Young\"";
    # print "\t" . int $aveYoungResMem ;
    # print "\n\"Avg Resident Memory (K) Old\"  ";
    # print "\t" . int $aveOldResMem ;
    # print "\n\"Avg Resident Memory (K) Total\"";
    # print "\t" . int $aveOverallResMem ;
    # print "\n\"Avg Resident Memory (K) Perm\" ";
    # print "\t" . int $avePermResMem ;
    # print "\n\"Avg Resident Memory (K) Major\"";
    # print "\t" . int ($aftMajorGcResMem / $majorGcCount);

	
	
	
	
  # ---------------------------------------------------------------------
  # For trends, we need to perform some calculations:
  # Each trend is the percent ERROR between the average of the last 
  #   <sampleSize> values and the average of the 1st <sampleSize> values.
  # ---------------------------------------------------------------------
  
#  #trendPartialIntervals
#    {
#    my $sampleSize = 3;
#    my $tmpStartAverage = getAverage(0, $sampleSize-1, @allMinorGcIntervals);
#    my $tmpEndAverage = getAverage($#allMinorGcIntervals-$sampleSize+1, $#allMinorGcIntervals, @allMinorGcIntervals);
#    my $tmpTrend = 0.0; 
#    print OUT "\n trendPartialGcIntervals";
#    if (($tmpStartAverage eq "NA") || ($tmpEndAverage eq "NA"))
#        {
#          print OUT "\tNA";
#        }
#    else
#        {
#      $tmpTrend = 100.0 * ($tmpEndAverage - $tmpStartAverage) / $tmpStartAverage;
#      print OUT "\t$tmpTrend\%";
#        }
#    }
#    
## Temp Var Block
#    { 
#    #trendFullIntervals
#    my $sampleSize = 3;
#    $sampleSize = int(($#allMajorGcIntervals+1)/2) if($#allMajorGcIntervals < 5);
#    $tmpStartAverage = getAverage(0, $sampleSize-1, @allMajorGcIntervals);
#    $tmpEndAverage = getAverage($#allMajorGcIntervals-$sampleSize+1, $#allMajorGcIntervals, @allMajorGcIntervals);
#    print OUT "\n trendFullGcIntervals";
#    if (($tmpStartAverage eq "NA") || ($tmpEndAverage eq "NA"))
#        {
#        print OUT "\tNA";
#        }
#    else
#        {
#        $tmpTrend = 100.0 * ($tmpEndAverage - $tmpStartAverage) / $tmpStartAverage;
#        print OUT "\t$tmpTrend\%";
#        }
#    } # End Full Ints. temp var block
#  
#  #trendPartialTime
#    {
#    my $sampleSize = 3;
#    $tmpStartAverage = getAverage(0, $sampleSize-1, @allMinorGcTime);
#    $tmpEndAverage = getAverage($#allMinorGcTime-$sampleSize+1, $#allMinorGcTime, @allMinorGcTime);
#    print OUT "\n trendPartialGcTime";
#    if (($tmpStartAverage eq "NA") || ($tmpEndAverage eq "NA"))
#        {
#        print OUT "\tNA";
#        }
#    else
#        {
#        $tmpTrend = 100.0 * ($tmpEndAverage - $tmpStartAverage) / $tmpStartAverage;
#        print OUT "\t$tmpTrend\%";
#        }
#    }
#    
## Temp Var Block
#    { 
#    #trendFullTime
#    my $sampleSize = 3;
#    $sampleSize = int(($#allMajorGcTime+1)/2) if($#allMajorGcTime < 5);
#    $tmpStartAverage = getAverage(0, $sampleSize-1, @allMajorGcTime);
#    $tmpEndAverage = getAverage($#allMajorGcTime-$sampleSize+1, $#allMajorGcTime, @allMajorGcTime);
#    print OUT "\n trendFullGcTime";
#    if (($tmpStartAverage eq "NA") || ($tmpEndAverage eq "NA"))
#        {
#        print OUT "\t\tNA";
#        }
#    else
#        {
#        $tmpTrend = 100.0 * ($tmpEndAverage - $tmpStartAverage) / $tmpStartAverage;
#        print OUT "\t$tmpTrend\%";
#        }
#    } # End full time temp var block
#
#  #trendYoungResMem
#    {
#    $tmpStartAverage = getAverage(0, $sampleSize-1, @allYoungResMem);
#    $tmpEndAverage = getAverage($#allYoungResMem-$sampleSize+1, $#allYoungResMem, @allYoungResMem);
#    print OUT "\n trendYoungResMem";
#    if (($tmpStartAverage eq "NA") || ($tmpEndAverage eq "NA"))
#        {
#        print OUT "\tNA";
#        }
#    else
#        {
#        $tmpTrend = 100.0 * ($tmpEndAverage - $tmpStartAverage) / $tmpStartAverage;
#        print OUT "\t$tmpTrend\%";
#        }
#    }
#    
## Temp Var Block
#    { 
#    #trendOldResMem
#    my $sampleSize = int(($#allOldResMem+1)/2) if($#allOldResMem < 5);
#    $tmpStartAverage = getAverage(0, $sampleSize-1, @allOldResMem);
#    $tmpEndAverage = getAverage($#allOldResMem-$sampleSize+1, $#allOldResMem, @allOldResMem);
#    print OUT "\n trendOldResMem";
#    if (($tmpStartAverage eq "NA") || ($tmpEndAverage eq "NA"))
#        {
#        print OUT "\tNA";
#        }
#    else
#        {
#        $tmpTrend = 100.0 * ($tmpEndAverage - $tmpStartAverage) / $tmpStartAverage;
#        print OUT "\t$tmpTrend\%";
#        }
#    } #end Old temp var block
#
#  #trendTotalResMem
#    {
#    $tmpStartAverage = getAverage(0, $sampleSize-1, @allOverallResMem);
#    $tmpEndAverage = getAverage($#allOverallResMem-$sampleSize+1, $#allOverallResMem, @allOverallResMem);
#    print OUT "\n trendTotalResMem";
#    if (($tmpStartAverage eq "NA") || ($tmpEndAverage eq "NA"))
#        {
#        print OUT "\tNA";
#        }
#    else
#        {
#        $tmpTrend = 100.0 * ($tmpEndAverage - $tmpStartAverage) / $tmpStartAverage;
#        print OUT "\t$tmpTrend\%";
#        } 
#    }
#    
## Temp Var Block
#    { 
#    #trendPermResMem
#    my $sampleSize = int(($#allPermResMem+1)/2) if($#allPermResMem < 5);
#    $tmpStartAverage = getAverage(0, $sampleSize-1, @allPermResMem);
#    $tmpEndAverage = getAverage($#allPermResMem-$sampleSize+1, $#allPermResMem, @allPermResMem);
#    print OUT "\n trendPermResMem";
#    if (($tmpStartAverage eq "NA") || ($tmpEndAverage eq "NA"))
#        {
#        print OUT "\tNA";
#        }
#    else
#        {
#        $tmpTrend = 100.0 * ($tmpEndAverage - $tmpStartAverage) / $tmpStartAverage;
#        print OUT "\t$tmpTrend\%";
#        }
#    } # End Perm temp var block
    
    }
print OUT "\n";
print OUT "\n";
close OUT;

print "Done!\n" if $verbose;
exit 0;

#------------------------------------------------------------
# Subroutines go here:
#   &usage
#   &chompLine
#   &getAverage
# -----------------------------------------------------------

# -----------------------------------------------------------
# Generic help message
# This routine also exits perl.
# -----------------------------------------------------------
sub usage {
# 80:    ---------+---------+---------+---------+---------+---------+---------+---------+
  print "\n";
  print "This script analyzes a single file for garbage collection (GC) data.\n";
  print "\n";
  print "Usage: perl $0 <switches> <fileName> [<saveLocation>] [<outBase>]\n";
  print "  fileName is the file to be scanned for GC data.\n";
  print "  saveLocation is a the location to which the summery file is saved.\n";  
  print "    The default save location is the current directory\n";
  print "  outBase is an optional prefix for the result file name (default $gcOutBase)\n";
  print "\n";
  print "Switches:  (Note: times below are in seconds since JVM start)\n";
  print "  -s <number> or -start <number>  -- start time for GC collection.\n";
  print "  -e <number> or -end <number>  -- end time for GC collection.\n";
  print "  -d <path> or -destination <path> -- Alternative to using <saveLocation> above.\n";
  print "  -b <outBase> or -base <outBase> -- Alternative to using <outBase> above.\n";
#  print "  -m or -multi -- parse for multiple formats (used for JRockit genpar setting).\n";
  print "\n";
  print "This script outputs, in order:\n";
  print "  The name/path to the file scanned,\n";
  print "  The average time between GC events (Total_Time_Between_GC's / Number_of_GC's),\n";
  print "  The average length of a GC event (Total_Time_in_GC / Number_of_GC's ),\n";
  print "  The average resident memory (AveResMem / Number_of_GC's ),\n";
  print "  The trend for the GC Intervals (the time between GC's),\n";
  print "  The trend for the GC Time (the length of the GC's),\n";
  print "  The trend for the resident memory (the size of the heap after collection),\n";
  print "\n";
  print "For more detailed information, see http://10.23.44.111/twiki/bin/view/Main/GcRollup\n";
  print "\n";
  # Note how I use an uninterpolated Perl string so that the dollar signs are OK
  print '$Id: gcRollup.pl,v 1.04 2007/08/08 13:50:12 jburke Exp $';
  exit 0;
}

# -----------------------------------------------------------
# chompLine
#
# Description: chomp() extended for MS-DOS madness
# Inputs: $line with some sorts of line termination
# Returns: same line without all the EOL cruft.
#
# Designed to work on both Unix- and MS-DOS- style files.
# -----------------------------------------------------------
sub chompLine( $ )
    {
    my $xline = shift;

    return undef if !defined($xline);
  
    chomp($xline);
    $xline =~ s/(.*)\r/$1/;
    return $xline;
    }

# -----------------------------------------------------------
# Purpose: Get average values within a range of an array
# Inputs: 
#   $start to $end inclusive -- number of samples to average over
#   @simpleStats -- array of statistics
# Returns: The average.  Negative means error occurred.
# -----------------------------------------------------------
sub getAverage
    {
    my ($start, $end, @simpleStats) = @_;
    my $result = 0.0;

    if( $start < 0 || $start > $end || $end > $#simpleStats )
      {
      return "NA";
      }
    
    for( my $i = $start; $i <= $end; $i ++)
        {
        $result += $simpleStats[$i];
        }
    
    return $result / ($end - $start + 1);
    }

# -----------------------------------------------------------
# $Log: gcRollup.pl,v $
# Current: $Id: gcRollup.pl,v 1.04 2007/08/08 13:50:12 jburke Exp $
# 
# Revision 1.04 2007/08/08 13:50:12 jburke
#  Added support for generational GC data (Sun JVM)
# Revision 1.03 2007/07/20 14:52:07 jburke
#  Fixed potential error in the GC Template, updated documentation
# Revision 1.02 2007/07/19 15:30:55 jburke
#  Changed format for invoking program, 
#  added saveFolder as an option
#  added reference to TWiki in help
# Revision 1.01 2007/07/19 10:05:00 jburke
#   Minor changes to -help display and comments within code
# Revision 1.0 2007/07/18 16:30:00 jburke
#   Created script (using code from rollup.pl)
