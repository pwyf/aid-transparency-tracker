Vagrant.configure(2) do |config|

  config.vm.box = "ubuntu/xenial64"

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

          # https://github.com/boxcutter/ubuntu/issues/82#issuecomment-260902424
          vb.customize [
              "modifyvm", :id,
              "--cableconnected1", "on",
          ]

        end

        config.vm.provision :shell, path: "vagrant/bootstrap.sh"

    end

end
