# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  # Where HA Proxy will live
  config.vm.define :proxy do |proxy_config|
    proxy_config.vm.box = "raring64"
    proxy_config.vm.box_url = "http://cloud-images.ubuntu.com/raring/current/raring-server-cloudimg-vagrant-amd64-disk1.box"
    proxy_config.vm.network :private_network, ip: "192.168.33.10"
  end

  # Where Gitlab will live
  #config.vm.define :vcs do |vcs_config|
  #  vcs_config.vm.box = "raring64"
  #  vcs_config.vm.box_url = "http://cloud-images.ubuntu.com/raring/current/raring-server-cloudimg-vagrant-amd64-disk1.box"
  #  vcs_config.vm.network :private_network, ip: "192.168.33.11"

  #  vcs_config.vm.provider "virtualbox" do |vb|
  #    # Use VBoxManage to customize the VM. For example to change memory:
  #    vb.customize ["modifyvm", :id, "--memory", "1024"]
  #  end
  #end

  # Where Jenkins will live
  #config.vm.define :ci do |ci_config|
  #  ci_config.vm.box = "raring64"
  #  ci_config.vm.box_url = "http://cloud-images.ubuntu.com/raring/current/raring-server-cloudimg-vagrant-amd64-disk1.box"
  #  ci_config.vm.network :private_network, ip: "192.168.33.12"

  #  ci_config.vm.provider "virtualbox" do |vb|
  #    # Use VBoxManage to customize the VM. For example to change memory:
  #    vb.customize ["modifyvm", :id, "--memory", "1024"]
  #  end
  #end

  # Where Apt-Cacher or Apt-Mirror will live
  config.vm.define :apt do |apt_config|
    apt_config.vm.box = "raring64"
    apt_config.vm.box_url = "http://cloud-images.ubuntu.com/raring/current/raring-server-cloudimg-vagrant-amd64-disk1.box"
    apt_config.vm.network :private_network, ip: "192.168.33.13"
  end

  config.vm.define :db do |db_config|
    db_config.vm.box = "raring64"
    db_config.vm.box_url = "http://cloud-images.ubuntu.com/raring/current/raring-server-cloudimg-vagrant-amd64-disk1.box"
    db_config.vm.network :private_network, ip: "192.168.33.11"

    db_config.vm.provider "virtualbox" do |vb|
      # Use VBoxManage to customize the VM. For example to change memory:
      vb.customize ["modifyvm", :id, "--memory", "1024"]
    end
  end

  config.vm.define :web0 do |web0_config|
    web0_config.vm.box = "raring64"
    web0_config.vm.box_url = "http://cloud-images.ubuntu.com/raring/current/raring-server-cloudimg-vagrant-amd64-disk1.box"
    web0_config.vm.network :private_network, ip: "192.168.33.100"
  end

  config.vm.define :web1 do |web1_config|
    web1_config.vm.box = "raring64"
    web1_config.vm.box_url = "http://cloud-images.ubuntu.com/raring/current/raring-server-cloudimg-vagrant-amd64-disk1.box"
    web1_config.vm.network :private_network, ip: "192.168.33.101"
  end
end
