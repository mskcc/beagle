pipeline {
  agent any

  stages {
      stage("Deploy to Dev") {
      input {
          message "Do you want to deploy to dev?"
          parameters {
              string(name: 'DEV_LOCATION', defaultValue: '/srv/services/beagle_dev/beagle', description: 'Where do you want to deploy?')

          }
      }
        steps {
        echo "deply to dev"
          //sshagent(credentials: ['a4d999a5-6318-4659-83be-3f148a5490ca']) {
          //  sh 'ssh  -o StrictHostKeyChecking=no  voyager@silo.mskcc.org "cd $DEV_LOCATION && git checkout develop && git pull && source run_restart.sh"'
          //sh 'ssh  -o StrictHostKeyChecking=no  voyager@silo.mskcc.org cd /srv/services/staging_voyager/beagle'

        //  }

        }
      }
      stage('Deploy to Stage') {
              input {
                  message "Do you want to deploy to stage?"
                  parameters {
                      string(name: 'STAGE_LOCATION', defaultValue: '/srv/services/staging_voyager/beagle', description: 'Where do you want to deploy?')

                  }
              }
              steps {
              sshagent(credentials: ['a4d999a5-6318-4659-83be-3f148a5490ca']) {
               sh 'ssh  -o StrictHostKeyChecking=no  voyager@silo.mskcc.org "cd $STAGE_LOCATION && git checkout develop && git pull && source run_restart.sh"'
              //sh 'ssh  -o StrictHostKeyChecking=no  voyager@silo.mskcc.org cd /srv/services/staging_voyager/beagle'

             }
              }
          }
  }
}
