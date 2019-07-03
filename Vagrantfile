Vagrant.configure(2) do |config|
  config.vm.define "pwyf" do |normal|

    config.vm.box = "ubuntu/bionic64"
    config.disksize.size = '15GB'

    config.vm.network "forwarded_port", guest: 8080, host: 8080
    config.vm.network "forwarded_port", guest: 5432, host: 5432

    config.vm.provider "virtualbox" do |vb|
      # Display the VirtualBox GUI when booting the machine
      vb.gui = false

      # Customize the amount of memory on the VM:
      vb.memory = "2048"

    end

    config.vm.provision :shell, path: "vagrant/bootstrap.sh"

  end

end
