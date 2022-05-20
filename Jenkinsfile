pipeline {
  agent any
  parameters {
    choice(name: 'SERVER', choices: ['silo', 'voyager'], description: 'Server')
    string(name: 'DIRECTORY', defaultValue: '/srv/services/beagle_dev/beagle', description: 'Directory')

   }
  stages {
      stage("Deploy") {

    steps {
        echo "Starting deployment"
          sshagent(credentials: ['a4d999a5-6318-4659-83be-3f148a5490ca']) {
            sh 'ssh  -o StrictHostKeyChecking=no  voyager@$SERVER.mskcc.org "cd $DIRECTORY && git checkout $BRANCH_NAME && git pull && source run_restart.sh"'
          //sh 'ssh  -o StrictHostKeyChecking=no  voyager@silo.mskcc.org cd /srv/services/staging_voyager/beagle'

          }

        }
      }

  }
}
