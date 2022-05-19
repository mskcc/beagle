pipeline {
  agent any

  stages {
  /*  stage("reading env variables") {
      steps {
        echo "The branch name is ${env.BRANCH_NAME}"
        echo "The build number is ${env.BUILD_NUMBER}"
      }
    }*/
      stage("Deploy to Dev") {
        steps {
        echo hello
          //sshagent(credentials: ['a4d999a5-6318-4659-83be-3f148a5490ca']) {
          //  sh 'ssh  -o StrictHostKeyChecking=no  voyager@silo.mskcc.org "cd /srv/services/beagle_dev/beagle && git checkout develop && git pull && source run_restart.sh"'
          //sh 'ssh  -o StrictHostKeyChecking=no  voyager@silo.mskcc.org cd /srv/services/staging_voyager/beagle'

          }

        }
      }
      stage('input Example') {
            input {
                message "Should we continue?"
                ok "Yes, we should."
                submitter "alice,bob"
                parameters {
                    string(name: 'PERSON', defaultValue: 'Mr Jenkins', description: 'Who should I say hello to?')
                }
            }
            steps {
                echo "Hello, ${PERSON}, nice to meet you."
            }
        }
  }
}
