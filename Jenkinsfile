pipeline {
  agent any
  parameters {
      choice(name: 'SERVER', choices: ['DEV', 'STAGE','PROD'], description: 'Server')

     }
  stages {
     stage("Config file "){
      steps {
    //  sshagent(credentials: ['a4d999a5-6318-4659-83be-3f148a5490ca']) {
      configFileProvider(
      [configFile(fileId: 'd5f1bfe7-5ec7-4916-86b5-e024a30c78f8', variable: 'CONFIG_FILE')]) {

      sh 'scp $CONFIG_FILE voyager@silo.mskcc.org:/home/pankeyd'
   }
//   }
    }
      }
      stage("Deploy to Dev") {
      when {
      expression { params.SERVER == 'DEV' }
    }
      steps {
        echo "deply to dev"
           sshagent(credentials: ['a4d999a5-6318-4659-83be-3f148a5490ca']) {
            sh 'ssh  -o StrictHostKeyChecking=no  voyager@silo.mskcc.org "cd /srv/services/beagle_dev/beagle && git checkout $BRANCH_NAME && git pull && source run_restart.sh"'

          }

        }
      }
      stage('Deploy to Stage') {
      when {
      expression { params.SERVER == 'STAGE' }
    }
            steps {
              echo "deply to stage"
            /*  sshagent(credentials: ['a4d999a5-6318-4659-83be-3f148a5490ca']) {
               sh 'ssh  -o StrictHostKeyChecking=no  voyager@silo.mskcc.org "cd /srv/services/staging_voyager/beagle && git checkout $BRANCH_NAME && git pull && source run_restart.sh"'

             } */
              }
          }
          stage('Deploy to Prod') {
          when {
          expression { params.SERVER == 'PROD' }
        }
                steps {
                  echo "deply to PROD"
                /*  sshagent(credentials: ['a4d999a5-6318-4659-83be-3f148a5490ca']) {
                   sh 'ssh  -o StrictHostKeyChecking=no  voyager@silo.mskcc.org "cd /srv/services/staging_voyager/beagle && git checkout $BRANCH_NAME && git pull && source run_restart.sh"'

                 } */
                  }
              }
  }
}
