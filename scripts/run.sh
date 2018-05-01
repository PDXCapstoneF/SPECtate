#!/bin/bash

###############################################################################
## 
## This script is ment to be called from goMLQ.sh each line being a run of SPECjbb2015 in MultiJVM mode with a specified number of groups 
## Run options are as follows.
#  ./run.sh [HBIR] [kitVersion] [tag] [JDK] [RTSTART] [JVMoptions] [NUM NODE] [DATA collection] [T1] [T2] [T3]"
#  ./run.sh [HBIR_RT] [kitVersion] [tag] [JDK] [RTSTART] [JVMoptions] [NUM NODE] [DATA collection] [T1] [T2] [T3]"
#  ./run.sh [PRESET] [kitVersion] [tag] [JDK] [TXrate] [Duration] [JVMoptions] [NUM NODE] [DATA collection] [T1] [T2] [T3]"
#  ./run.sh [LOADLEVEL] [kitVersion] [tag] [JDK] [RTSTART] [duration] [JVMoptions] [NUM NODE] [DATA collection] [T1] [T2] [T3]"
#  

function pause(){
   read -p "$*"
}


echo "running with this number of parameters:$#"

# Default Run Type

if [ $1 = "HBIR" ] || [ $1 = "HBIR_RT" ] && [ $# = 11 ]; then
echo  "run type is HBIR or HBIR_RT"
  RUN_TYPE=$1
  KITVER=$2
  ID_TAG=$3
  JVM=$4
  RT_CURVE=$5
  USR_JVM_OPTS=$6
  GROUPCOUNT=$7
  DATA=$8
  TIER1=$9
  TIER2=${10}
  TIER3=${11}
 
  sed -e "s/<<HBIR_TYPE>>/$RUN_TYPE/g" -e "s/<<T1>>/$TIER1/g" -e "s/<<T2>>/$TIER2/g" -e "s/<<T3>>/$TIER3/g" -e "s/<<GROUP_COUNT>>/$GROUPCOUNT/g" -e "s/<<RT_CURVE_START>>/$RT_CURVE/g" .HBIR_RT.props > specjbb2015.props


elif [ $1 = "PRESET" ] && [ $# = 12 ]; then
echo  "run type is PRESET"
  RUN_TYPE=$1
  KITVER=$2
  ID_TAG=$3
  JVM=$4
  PRESET_IR=$5
  DURATION=$(echo "$6*1000" | bc) 
  USR_JVM_OPTS=$7
  GROUPCOUNT=$8
  DATA=$9
  TIER1=${10}
  TIER2=${11}
  TIER3=${12}
  
  sed -e "s/<<T1>>/$TIER1/g" -e "s/<<T2>>/$TIER2/g" -e "s/<<T3>>/$TIER3/g" -e "s/<<GROUP_COUNT>>/$GROUPCOUNT/g" -e "s/<<PRESET_IR>>/$PRESET_IR/g" -e "s/<<DURATION>>/$DURATION/g" .PRESET.props > specjbb2015.props


elif [ $1 = "LOADLEVEL" ] && [ $# = 12 ]; then
echo  "run type is LOADLEVEL"

  RUN_TYPE=$1
  KITVER=$2
  ID_TAG=$3
  JVM=$4
  RT_CURVE=$5
  LL_DURATION_MIN=$(echo "$6*1000" | bc) 
  LL_DURATION_MAX=$(echo "$6*1000" | bc) 
  USR_JVM_OPTS=$7
  GROUPCOUNT=$8
  DATA=$9
  TIER1=${10}
  TIER2=${11}
  TIER3=${12}


  sed -e "s/<<T1>>/$TIER1/g" -e "s/<<T2>>/$TIER2/g" -e "s/<<T3>>/$TIER3/g" -e "s/<<GROUP_COUNT>>/$GROUPCOUNT/g" -e "s/<<LL_DUR_MIN>>/$LL_DURATION_MIN/g" -e "s/<<LL_DUR_MAX>>/$LL_DURATION_MAX/g" -e "s/<<RT_CURVE_START>>/$RT_CURVE/g" .LOADLEVELS.props > specjbb2015.props


else
  echo  "run type is invalid"
  echo " invalid number of arguments or invalid Run Type."
  echo " Usage:"
  echo " ./run.sh [HBIR] [kitVersion] [tag] [JDK] [RTSTART] [JVMoptions] [NUM NODE] [DATA collection] [T1] [T2] [T3]"
  echo " ./run.sh [HBIR_RT] [kitVersion] [tag] [JDK] [RTSTART] [JVMoptions] [NUM NODE] [DATA collection] [T1] [T2] [T3]"
  echo " ./run.sh [PRESET] [kitVersion] [tag] [JDK] [TXrate] [Duration] [JVMoptions] [NUM NODE] [DATA collection] [T1] [T2] [T3]"
  echo " ./run.sh [LOADLEVEL] [kitVersion] [tag] [JDK] [RTSTART] [duration] [JVMoptions] [NUM NODE] [DATA collection] [T1] [T2] [T3]"
  echo "$1, $2, $3, $4, $5,$6, $7, $8, $9, ${10}, ${11}, ${12}, ${13}, ${14}, ${15}"
  echo " "
  echo " kit version is directory of kit"
  echo " TAG is just a tag or ID to clarify run "
  echo " point to start RT curve"
  echo " JVM options are additional options to be passed to the JVM."
  echo " Number of Nodes is the number of NUMA Nodes to use"
  exit
fi

  JDK=${JVM%-*}

echo "JDK version is: $JDK"

echo "JDK version is: $JDK"

 if [ "$JDK" == "jdk1.9" ]; then
# Options are changing between JDK9 builds -addmods changes to --add-modules

  JAVA_OPTS="-showversion --add-modules java.xml.bind -XX:+UseLargePages -XX:LargePageSizeInBytes=2m -XX:+AggressiveOpts -XX:-UseAdaptiveSizePolicy -XX:+AlwaysPreTouch -XX:-UseBiasedLocking -XX:+UseParallelOldGC -XX:SurvivorRatio=28 -XX:TargetSurvivorRatio=95 -XX:MaxTenuringThreshold=15"
     OPTS_TI="-showversion -server -XX:+UseParallelOldGC --add-modules java.xml.bind -Xmx4g -Xms4g -Xmn3584m $GC_PRINT_OPTS" 
     OPTS_CTL="-server -showversion -XX:+UseParallelOldGC --add-modules java.xml.bind -mx2g -Xms2g -Xmn1536m $GC_PRINT_OPTS $SPEC_OPTS" 
     JAVA=/workloads/JVM/$JVM/bin/java

    #-XX:+UnlockDiagnosticVMOptions -XX:+PrintAssembly

elif [ "$JDK" == "jdk1.8" ]; then
     JAVA=/workloads/JVM/$JVM/bin/java
     JAVA_OPTS="-showversion -server -XX:+UseLargePages -XX:LargePageSizeInBytes=2m -XX:+AggressiveOpts -XX:-UseAdaptiveSizePolicy -XX:+AlwaysPreTouch -XX:-UseBiasedLocking -XX:+UseParallelOldGC -XX:SurvivorRatio=28 -XX:TargetSurvivorRatio=95 -XX:MaxTenuringThreshold=15"
     OPTS_TI="-server -showversion -Xmx6g -Xms6g -Xmn1g $GC_PRINT_OPTS" 
     OPTS_CTL="-server -showversion -Xmx3g -Xms3g -Xmn2560m $GC_PRINT_OPTS $SPEC_OPTS" 
elif [ "$JDK" == "jdk1.7" ]; then
     JAVA_OPTS="-showversion -server -XX:+UseLargePages -XX:LargePageSizeInBytes=2m -XX:+AggressiveOpts -XX:-UseAdaptiveSizePolicy -XX:+AlwaysPreTouch -XX:-UseBiasedLocking -XX:+UseParallelOldGC -XX:SurvivorRatio=28 -XX:TargetSurvivorRatio=95 -XX:MaxTenuringThreshold=15"
else
     echo "invalid JVM"
fi 
  OPTS_BE="$JAVA_OPTS $USR_JVM_OPTS $GC_PRINT_OPTS"


  read RUN_NUM < .run_number
  echo "$RUN_NUM + 1" | bc > .run_number
  echo "RUN NUMBER is :$RUN_NUM"


  TAG=${RUN_NUM}_${RUN_TYPE}_${JVM}_${ID_TAG}_${DATA}_${TIER1}_${TIER2}_${TIER3} 
  #Set JAVA to correct path  
  #JAVA=/workloads/JVM/$JVM/bin/java


  ### Create results directory and
  ### copy config to result dir to have full list of settings
  BINARIES_DIR=$(pwd)/$KITVER
  echo "This is the BINARY_DIR $BINARIES_DIR"
  RESULTDIR=$BINARIES_DIR/$TAG
  echo "This is the RESULTDIR $RESULTDIR"
  mv -f specjbb2015.props $BINARIES_DIR/config/
  pushd $KITVER
  pwd
  mkdir $RESULTDIR
  cp -r config $RESULTDIR
  pushd $RESULTDIR

  SUT_INFO=sut.txt
  echo " " > $SUT_INFO
  echo "##############################################################" >> $SUT_INFO
  echo "##########General Options ####################################" >> $SUT_INFO
  echo "##########General Options ####################################"
  echo "ID tag given is:: $TAG" >> $SUT_INFO
  echo "ID tag given is:: $TAG"
  echo "Type of data collection we are doing is:: $DATA" >> $SUT_INFO
  echo "Type of data collection we are doing is:: $DATA"
  echo "Number of NUMA Nodes using:: $GROUPCOUNT" >> $SUT_INFO
  echo "Number of NUMA Nodes using:: $GROUPCOUNT"
  echo "Additional JVM options:: $JVM_OPTS" >> $SUT_INFO
  echo "Additional JVM options:: $JVM_OPTS" 
  echo "All JVM options:: $OPTS_BE" >> $SUT_INFO
  echo "All JVM options:: $OPTS_BE" 
  echo "Controller JVM options:: $OPTS_CTL" >> $SUT_INFO
  echo "Controller JVM options:: $OPTS_CTL" 
  echo "Injector JVM options:: $OPTS_TI" >> $SUT_INFO
  echo "Injector JVM options:: $OPTS_TI" 
  echo "Full path of JAVA used:: $JAVA" >> $SUT_INFO
  echo "Full path of JAVA used:: $JAVA" 

  echo "##################################################################"
  echo "##################################################################" >> $SUT_INFO
  echo "##########SPECjbb2015 Options ####################################" >> $SUT_INFO
  echo "Kit version we are using:: $KITVER" >> $SUT_INFO
  echo "Kit version we are using:: $KITVER"
  echo "Starting RT curve at $RT_CURVE percent" >> $SUT_INFO
  echo "Starting RT curve at $RT_CURVE percent"
  echo "Number of Fork Join Threads to use on Tier1:: $TIER1" >> $SUT_INFO
  echo "Number of Fork Join Threads to use on Tier1:: $TIER1"
  echo "Number of Fork Join Threads to use on Tier2:: $TIER2" >> $SUT_INFO
  echo "Number of Fork Join Threads to use on Tier2:: $TIER2"
  echo "Number of Fork Join Threads to use on Tier3:: $TIER3" >> $SUT_INFO
  echo "Number of Fork Join Threads to use on Tier3:: $TIER3"
  echo "Groups count: $GROUPCOUNT" >> $SUT_INFO
  echo "Groups count: $GROUPCOUNT"
  echo "JVM options for Controller:$OPTS_CTL" >> $SUT_INFO
  echo "JVM options for Controller:$OPTS_CTL"
  echo "JVM options for Injector:$OPTS_TI" >> $SUT_INFO
  echo "JVM options for Injector:$OPTS_TI"
  echo "">>$SUT_INFO
  echo "">>$SUT_INFO 
  echo "************Latencies*********************************">>$SUT_INFO



   # Log system info to the SUT_INFO
  

  if [ $DATA != "NONE" ]; then
     echo "Launching Data collection"
     ../../data.sh $DATA $RESULTDIR $RUN_NUM $RUN_TYPE > datacollection.log &
  fi


  if [ "$DATA" == "ALL" ] || [ "$DATA" == "SEP" ]; then
      echo "Doing SEP data collection"
      SEP="-agentpath:/workloads/JVM/libjvmtisym/libjvmtisym.so=ofile=$BE_NAME.jsym"
  fi

  #echo "************Latencies*********************************">>$SUT_INFO
  #echo "***running mlc for Latencies*********************************"
  #/workloads/SPECjbb2015/mlc >>$SUT_INFO
  #echo "">>$SUT_INFO
  #echo "">>$SUT_INFO
  echo "************Memory Config*********************************">>$SUT_INFO
         dmidecode | grep MHz >>$SUT_INFO
  echo "**********************************************************"

  echo "Launching SPECjbb2015 in MultiJVM mode..."
  
 # vmstat -nt 1 > $RUN_NUM.vmstat.log &
 OUT=controller.out
 LOG=controller.log
 TI_JVM_COUNT=1

 uname -a >> $SUT_INFO; numactl --hardware >> $SUT_INFO; cat /proc/meminfo >> $SUT_INFO; cat /proc/cpuinfo >> $SUT_INFO;
     
 # start Controller on this host
 echo "Start Controller JVM"
 echo "$JAVA $OPTS_C -jar ../specjbb2015.jar -m MULTICONTROLLER"
 #if [ "$DATA" == "SEP" ]; then
 if [ "$DATA" == "ALL" ] || [ "$DATA" == "SEP" ]; then
     echo "Doing SEP data collection"
     SEPC="-agentpath:/workloads/JVM/libjvmtisym/libjvmtisym.so=ofile=Controller.jsym"
 fi
      
 if [ "$JDK" == "jdk1.9" ]; then   # if JDK9 GC log
   echo "$JAVA $OPTS_CTL -Xlog:gc*:Ctrlr.GC.log -jar ../specjbb2015.jar -m MULTICONTROLLER" >> $SUT_INFO

     $JAVA $OPTS_CTL $SEPC -Xlog:gc*:Ctrlr.GC.log -jar ../specjbb2015.jar -m MULTICONTROLLER 2>$LOG > $OUT &
 else    # if JDK8 gc log
     $JAVA $OPTS_CTL -Xloggc:Ctrlr.GC.log -jar ../specjbb2015.jar -m MULTICONTROLLER 2>$LOG > $OUT &
 fi
 
 sleep 5
 ##$JAVA -Dspecjbb.controller.host=localhost -jar specjbb2015.jar -m TIMESERVER

 CTRL_PID=$!
 echo "Controller PID = $CTRL_PID"

 # 5 sec should be enough to initialize Controller
 # set bigger delay if needed
 echo "Wait while Controller starting ..."
 sleep 5

 echo "group count is $GROUPCOUNT"

 for ((gnum=1; $gnum<$GROUPCOUNT+1; gnum=$gnum+1)); do

       GROUPID=Group$gnum
       echo -e "\nStarting JVMs from $GROUPID:"

       node=`expr "$gnum" - 1`
       #NewNode=$(($node%$GROUP_COUNT));
       #For COD enable
       NewNode=$(($node%4));
       #For COD disable
       #NewNode=$(($node%2)); 
       echo "******$node ******* $NewNode****"

       NUMAON="numactl --cpunodebind=$NewNode --localalloc"

       echo "TI_JVM_COUNT is $TI_JVM_COUNT"
       for ((jnum=1; $jnum<$TI_JVM_COUNT+1; jnum=$jnum+1)); do

           JVMID=JVM$jnum
           TI_NAME=$GROUPID.TxInjector.$JVMID
           if [ "$DATA" == "ALL" ] || [ "$DATA" == "SEP" ]; then
           #if [ "$DATA" == "SEP" ]; then
               echo "Doing SEP data collection"
               SEPTx="-agentpath:/workloads/JVM/libjvmtisym/libjvmtisym.so=ofile=$TI_NAME.jsym"
           fi

           # start TxInjector on this host
           echo "$NUMAON $JAVA $OPTS_TI -jar ../specjbb2015.jar -m TXINJECTOR -G=$GROUPID -J=$JVMID" >> $SUT_INFO

           if [ "$JDK" == "jdk1.9" ]; then   # if JDK9 GC log
              $NUMAON $JAVA $OPTS_TI $SEPTx -Xlog:gc*:$TI_NAME.GC.log -jar ../specjbb2015.jar -m TXINJECTOR -G=$GROUPID -J=$JVMID > $TI_NAME.log 2>&1 &
           else
              $NUMAON $JAVA $OPTS_TI $SEPTx -Xloggc:$TI_NAME.GC.log -jar ../specjbb2015.jar -m TXINJECTOR -G=$GROUPID -J=$JVMID -ikv > $TI_NAME.log 2>&1 &
           fi
       done
       

       for ((jnum=1+$TI_JVM_COUNT; $jnum<$TI_JVM_COUNT+2; jnum=$jnum+1)); do

          JVMID=JVM$jnum
          BE_NAME=$GROUPID.Backend.$JVMID

          if [ "$DATA" == "ALL" ] || [ "$DATA" == "SEP" ]; then
          #if [ "$DATA" == "SEP" ]; then
               echo "Doing SEP data collection"
               SEPBE="-agentpath:/workloads/JVM/libjvmtisym/libjvmtisym.so=ofile=$BE_NAME.jsym"
          fi

          # start Backend on local SUT host
          echo "$NUMAON $JAVA $OPTS_BE -Xloggc:$BE_NAME.GC.log -jar ../specjbb2015.jar -m BACKEND -G=$GROUPID -J=$JVMID" >>$SUT_INFO
           if [ "$JDK" == "jdk1.9" ]; then   # if JDK9 GC log
              $NUMAON $JAVA $SEPBE $OPTS_BE -Xlog:gc*:$BE_NAME.GC.log -jar ../specjbb2015.jar -m BACKEND -G=$GROUPID -J=$JVMID > $BE_NAME.log 2>&1 &
           else
              $NUMAON $JAVA $SEPBE $OPTS_BE -Xloggc:$BE_NAME.GC.log -jar ../specjbb2015.jar -m BACKEND -G=$GROUPID -J=$JVMID -ikv > $BE_NAME.log 2>&1 &
              BE_PID=$!
              echo "dumping PageMap for Backend PID = $BE_PID"
	      (sleep 600 ; ../datapgmap $BE_PID > $BE_NAME.$BE_PID.dump.log) &
           fi
       done
  done

  

  echo "Wait while specjbb2015 is running ..."
  echo "Press Ctrl-break to stop the run"
  wait $CTRL_PID

  echo "Controller stopped"
  echo "Kill all related proceses"
  sleep 15
  

  #$JAVA -Xms4g -Xmx4g -jar ../specjbb2015.jar -m REPORTER -s specjbb2015*.data.gz -l 3

  ../KillDataCollection.sh
  sleep 15
  killall java
  cp result/specjbb2015*/report*/*.html .
  uname -a >> $SUT_INFO; numactl --hardware >> $SUT_INFO; cat /proc/meminfo >> $SUT_INFO; cat /proc/cpuinfo >> $SUT_INFO;




exit 0
