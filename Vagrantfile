# -*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "ubuntu/trusty64"
  config.vm.box_url = "ubuntu/trusty64"
  config.vm.network :forwarded_port, guest: 8001, host: 8001
  config.vm.network :forwarded_port, guest: 8081, host: 8081
  config.vm.network :forwarded_port, guest: 9091, host: 9091
  config.vm.network :private_network, ip: "192.168.33.16"

  config.vm.provider :virtualbox do |vb|
    vb.customize ["modifyvm", :id, "--name", "worldmap-1.5", "--memory", "4096"]
  end

  config.vm.synced_folder ".", "/home/vagrant/cga-worldmap"

end
