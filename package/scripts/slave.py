#import status properties defined in -env.xml file from status_params class

import sys, os, pwd, signal, time
from resource_management import *
from resource_management.core.base import Fail
from resource_management.core.exceptions import ComponentIsNotRunning
from subprocess import call
import cPickle as pickle

class Slave(Script):

  #Call setup.sh to install the service
  def install(self, env):
    import params

    # First, download the Alluxio artifact
    cmd = '/bin/mkdir -p ' + params.alluxio_package_dir + '/files/'
    Execute('echo "Running ' + cmd + '"')
    Execute(cmd)
    # download and move the file to the correct directory
    cmd = '/usr/bin/wget -nc ' + params.alluxio_artifact
    Execute('echo "Running ' + cmd + '"')
    Execute(cmd)
    cmd = '/bin/cp alluxio* ' + params.alluxio_package_dir + '/files/'
    Execute('echo "Running ' + cmd + '"')
    Execute(cmd)

    # Install packages listed in metainfo.xml
    self.install_packages(env)

    # Create the base_dir/alluxio dir
    cmd = '/bin/mkdir' + ' -p ' + params.base_dir
    Execute('echo "Running ' + cmd + '"')
    Execute(cmd)

    #extract archive and symlink dirs
    cmd = '/bin/tar' + ' -zxf ' + params.alluxio_package_dir + 'files/' +  params.alluxio_archive_file + ' --strip 1 -C ' + params.base_dir
    Execute('echo "Running ' + cmd + '"')
    Execute(cmd)

    cmd = '/bin/ln' + ' -s ' + params.base_dir + ' ' + params.usr_base + 'current/alluxio'
    Execute('echo "Running ' + cmd + '"')

    try:
      Execute(cmd)
    except:
      pass

    # TODO don't set this up twice; consider skipping all of this if zfs is already installed
    # Create two roughly equal-sized partitions from a device
    # TODO get this disk name from alluxio params
    # TODO implement an alluxio param for ZFS?
    zfs_device = params.config['configurations']['alluxio-env']['alluxio.worker.zfs.device']
    #Execute('echo -e "n\np\n1\n\n1855467725\nn\np\n2\n\n\n\nw\n" | fdisk /dev/nvme0n1')
    Execute('echo -e "n\np\n1\n\n1855467725\nn\np\n2\n\n\n\nw\n" | fdisk /dev/' + zfs_device)
    # install ZFS
    Execute('sed -i "s/releasever=latest/releasever=2017.03/g" /etc/yum.conf')
    Execute('yum install -y "kernel-devel-uname-r == $(uname -r)"')
    Execute('yum install -y http://download.zfsonlinux.org/epel/zfs-release.el6.noarch.rpm')
    Execute('yum install -y zfs')
    Execute('modprobe zfs')
    # create a zpool with a mirror
    zfs_mirror_1 = zfs_device + "p1"
    zfs_mirror_2 = zfs_device + "p2"
    Execute('zpool create -f alluxio mirror ' + zfs_mirror_1 + ' ' + zfs_mirror_2)
    # create the filesystem to give to Alluxio
    Execute('zfs create alluxio/fs')
    Execute('zfs set compression=off alluxio/fs')
    Execute('chmod -R 777 /alluxio/fs')

    self.configure(env)

  def configure(self, env):
    import params
    env.set_params(params)

    alluxio_config_dir = params.base_dir + '/conf/'
    alluxio_libexec_dir = params.base_dir + '/libexec/'

    File(format("{alluxio_config_dir}/alluxio-site.properties"),
          owner='root',
          group='root',
          mode=0700,
          content=Template('alluxio-site.properties.template', conf_dir=alluxio_config_dir)
    )
    # Need to configure the alluxio-site file
    alluxio_site_file = format("{alluxio_config_dir}/alluxio-site.properties")
    alluxio_site = params.config['configurations']['alluxio-env']
    def configure_value_in_alluxio_site_file(property_name, property_value):
      replace_cmd = format("sed -i 's|^{property_name}=.*$|{property_name}={property_value}|'")
      cmd = replace_cmd + ' ' + alluxio_site_file
      Execute('echo "Running cmd: ' + cmd + '"')
      Execute(cmd)

    # Configure the alluxio master hostname
    configure_value_in_alluxio_site_file("alluxio.master.hostname", params.alluxio_master[0])

    for k, v in alluxio_site.items():
      configure_value_in_alluxio_site_file(k,v)

  #Call start.sh to start the service
  def start(self, env):
    import params

    # Create the log dir
    cmd = "mkdir -p " + params.log_dir
    Execute(cmd)

    cmd = params.base_dir + '/bin/alluxio-start.sh ' + 'worker' + ' NoMount'
    Execute('echo "Running cmd: ' + cmd + '"')
    Execute(cmd)

    # Create pid file - note check_process_status expects a SINGLE int in the file
    cmd = "mkdir -p " + params.pid_dir
    Execute(cmd)
    cmd = "echo `ps -A -o pid,command | grep -i \"[j]ava\" | grep AlluxioWorker | awk '{print $1}'`> " + params.pid_dir + "/AlluxioWorker.pid"
    Execute(cmd)
    pid_file = format("{params.pid_dir}/AlluxioWorker.pid")

  #Called to stop the service using the pidfile
  def stop(self, env):
    import params
    #execute the stop script
    cmd = params.base_dir + '/bin/alluxio-stop.sh local'

    Execute('echo "Running cmd: ' + cmd + '"')
    Execute(cmd)

  #Called to get status of the service using the pidfile
  def status(self, env):
    import params
    pid_file = format("{params.pid_dir}/AlluxioWorker.pid")
    check_process_status(pid_file)

if __name__ == "__main__":
  Slave().execute()
