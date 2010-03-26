#!/bin/bash

# Determine if we are running in a terminal
tty -s
if [ $? -eq 0 ]; then
  # run verbose
  HG_OPTS="-v"
  TAR_OPTS="-v"
  ZIP_OPTS=""
else
  HG_OPTS=""
  TAR_OPTS=""
  ZIP_OPTS="-q"
fi

CWD=`pwd`
HG_REPOS="http://bitbucket.org/uche/amara/|amara http://bitbucket.org/uche/akara/|akara"
DATE=`python -c "from time import *; print strftime('%Y-%m-%d',localtime(time()))"`
SNAPSHOT_DIR=/var/ftp/pub/nightlies

function make_snapshot() {
  param=$1
  repo=`echo ${param} | cut -f 1 -d "|"`
  name=`echo ${param} | cut -f 2 -d "|"`

  echo Creating snapshot for ${name} from ${repo}

  # Get the current version
  hg ${HG_OPTS} clone ${repo} ${name}

  # Create the archives
  filename=${name}-${DATE}
  tar $TAR_OPTS -cjf ${SNAPSHOT_DIR}/${filename}.tar.bz2 ${name}
  tar $TAR_OPTS -czf ${SNAPSHOT_DIR}/${filename}.tar.gz ${name}
  zip $ZIP_OPTS -r ${SNAPSHOT_DIR}/${filename}.zip ${name}

  # Update symbolic links
  pushd $SNAPSHOT_DIR > /dev/null
  formats="tar.bz2 tar.gz zip"
  for format in $formats; do
    ln -sf ${filename}.${format} 00-${name}-latest.${format}
  done
  popd > /dev/null
}

mkdir /tmp/snapshots
cd /tmp/snapshots

for param in $HG_REPOS; do
  make_snapshot $param
done

# cleanup
rm -rf /tmp/snapshots
find ${SNAPSHOT_DIR} -mtime +30 -exec rm {} \;

cd ~/akara-sumo
rm akara-sumo*.tar*
python build.py
gzip akara-sumo*.tar
SUMOFILE=`ls -1 akara-sumo*.tar.gz | python -c "import sys; sys.stdout.write(sys.stdin.read().strip())"`
#echo GRIPPO ${SUMOFILE}
if [ -f ~/akara-sumo/${SUMOFILE} ]
then
  mv ~/akara-sumo/${SUMOFILE} ${SNAPSHOT_DIR}
  #echo ln -sf ${SNAPSHOT_DIR}/${SUMOFILE} ${SNAPSHOT_DIR}/00-akara-sumo-latest.tar.gz
  cd ${SNAPSHOT_DIR}
  echo ln -sf ${SUMOFILE} 00-akara-sumo-latest.tar.gz
  ln -sf ${SUMOFILE} 00-akara-sumo-latest.tar.gz
fi

# restore initial directory
cd $CWD

