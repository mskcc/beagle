pipeline {
  agent any

  stages {
   stage("reading env variables") {
      steps {
        echo "The branch name is ${env.BRANCH_NAME}"
        echo "The build number is ${env.BUILD_NUMBER}"
      }
    }
      stage("Deploy to Dev") {
        steps {
        echo "deply to dev"
          //sshagent(credentials: ['a4d999a5-6318-4659-83be-3f148a5490ca']) {
          //  sh 'ssh  -o StrictHostKeyChecking=no  voyager@silo.mskcc.org "cd /srv/services/beagle_dev/beagle && git checkout develop && git pull && source run_restart.sh"'
          //sh 'ssh  -o StrictHostKeyChecking=no  voyager@silo.mskcc.org cd /srv/services/staging_voyager/beagle'

        //  }

        }
      }
      stage('Example') {
              input {
                  message "Should we continue to stage?"
                  ok "Yes"
                //  submitter "alice,bob"
                  parameters {
                      //string(name: 'PERSON', defaultValue: 'Mr Jenkins', description: 'Who should I say hello to?')
                      string(name: 'DEPLOY_LOCATION', defaultValue: 'cd /srv/services/beagle_dev/beagle', description: 'Where do you want to deploy?')

                  }
              }
              steps {
              sshagent(credentials: ['a4d999a5-6318-4659-83be-3f148a5490ca']) {
               sh 'ssh  -o StrictHostKeyChecking=no  voyager@silo.mskcc.org "cd ${DEPLOY_LOCATION} && git checkout develop && git pull && source run_restart.sh"'
              //sh 'ssh  -o StrictHostKeyChecking=no  voyager@silo.mskcc.org cd /srv/services/staging_voyager/beagle'

             }
              }
          }
  }
}
