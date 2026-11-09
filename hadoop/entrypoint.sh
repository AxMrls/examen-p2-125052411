#!/bin/sh
set -eu
mkdir -p /run/sshd /shared-ssh /home/hadoop/.ssh /evidencias
chown hadoop:hadoop /evidencias /data/output
ssh-keygen -A
if [ ! -f /shared-ssh/id_ed25519 ]; then
  ssh-keygen -t ed25519 -N '' -f /shared-ssh/id_ed25519 -q
fi
chmod 600 /shared-ssh/id_ed25519
chmod 644 /shared-ssh/id_ed25519.pub
cp /shared-ssh/id_ed25519 /home/hadoop/.ssh/id_ed25519
cp /shared-ssh/id_ed25519.pub /home/hadoop/.ssh/authorized_keys
chmod 700 /home/hadoop/.ssh
chmod 600 /home/hadoop/.ssh/authorized_keys /home/hadoop/.ssh/id_ed25519
chown -R hadoop:hadoop /home/hadoop/.ssh /shared-ssh
/usr/sbin/sshd
# Se mantiene SSH disponible mientras el pipeline se ejecuta como usuario hadoop.
su -s /bin/sh hadoop -c '/opt/proyecto/scripts/ejecutar_pipeline.sh' || echo 'ERROR: pipeline incompleto; consultar logs de hadoop.' >&2
exec tail -f /dev/null
