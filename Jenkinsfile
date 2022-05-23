
pipeline {
  agent any
  parameters {
    choice(name: 'SERVER', choices: ['DEV', 'STAGE'], description: 'Server')

   }
  stages {
      stage("Deploy to Dev") {
      when {
            expression { params.SERVER == 'DEV' }
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
      when {
            expression { params.SERVER == 'STAGE' }
          }
      }
              steps {
              echo "deply to stage"
            //  sshagent(credentials: ['a4d999a5-6318-4659-83be-3f148a5490ca']) {
            //   sh 'ssh  -o StrictHostKeyChecking=no  voyager@silo.mskcc.org "cd $STAGE_LOCATION && git checkout develop && git pull && source run_restart.sh"'
              //sh 'ssh  -o StrictHostKeyChecking=no  voyager@silo.mskcc.org cd /srv/services/staging_voyager/beagle'

            // }
              }
          }
  }
}
