pipeline {
  agent any

  stages {
      stage("Deploy to Dev") {
        steps {
        echo "deply to dev"
          //sshagent(credentials: ['a4d999a5-6318-4659-83be-3f148a5490ca']) {
          //  sh 'ssh  -o StrictHostKeyChecking=no  voyager@silo.mskcc.org "cd /srv/services/beagle_dev/beagle && git checkout develop && git pull && source run_restart.sh"'
          //sh 'ssh  -o StrictHostKeyChecking=no  voyager@silo.mskcc.org cd /srv/services/staging_voyager/beagle'

        //  }

        }
      }
      stage('Deploy to Stage') {
              input {
                  message "Should we continue to stage?"
                  ok "Yes"
                  parameters {
                      string(name: 'DEPLOY_LOCATION', defaultValue: 'cd /srv/services/beagle_dev/beagle', description: 'Where do you want to deploy?')

                  }
              }
              steps {
              sshagent(credentials: ['a4d999a5-6318-4659-83be-3f148a5490ca']) {
               sh 'ssh  -o StrictHostKeyChecking=no  voyager@silo.mskcc.org "cd $DEPLOY_LOCATION && git checkout develop && git pull && source run_restart.sh"'
              //sh 'ssh  -o StrictHostKeyChecking=no  voyager@silo.mskcc.org cd /srv/services/staging_voyager/beagle'

             }
              }
          }
  }
}
