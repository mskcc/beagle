pipeline {
  agent any

  stages {
      stage("Deploy") {
      parameters {
        string(name: 'DIRECTORY', defaultValue: '/srv/services/beagle_dev/beagle', description: 'Directory')


        choice(name: 'SERVER', choices: ['silo', 'voyager'], description: 'Server')

    }
        steps {
        echo "Starting deployment"
          //sshagent(credentials: ['a4d999a5-6318-4659-83be-3f148a5490ca']) {
          //  sh 'ssh  -o StrictHostKeyChecking=no  voyager@$SERVER.mskcc.org "cd $DIRECTORY && git checkout $BRANCH_NAME && git pull && source run_restart.sh"'
          //sh 'ssh  -o StrictHostKeyChecking=no  voyager@silo.mskcc.org cd /srv/services/staging_voyager/beagle'

        //  }

        }
      }
    /*  stage('Deploy to Stage') {
              input {
                  message "Do you want to deploy to stage?"
                  parameters {
                      string(name: 'STAGE_LOCATION', defaultValue: '/srv/services/staging_voyager/beagle', description: 'Where do you want to deploy?')

                  }
              }
              steps {
              echo "deply to stage"
            //  sshagent(credentials: ['a4d999a5-6318-4659-83be-3f148a5490ca']) {
            //   sh 'ssh  -o StrictHostKeyChecking=no  voyager@silo.mskcc.org "cd $STAGE_LOCATION && git checkout develop && git pull && source run_restart.sh"'
              //sh 'ssh  -o StrictHostKeyChecking=no  voyager@silo.mskcc.org cd /srv/services/staging_voyager/beagle'

            // }
              }
          } */
  }
}
