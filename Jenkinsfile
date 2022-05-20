pipeline {
  agent any
/*  parameters {
    choice(name: 'AERVER', choices: ['silo', 'voyager'], description: 'Server')
    string(name: 'DIRECTORY', defaultValue: '/srv/services/beagle_dev/beagle', description: 'Directory')

   } */
  stages {
      stage("Deploy") {

    steps {
      script {
    properties([
                      parameters([
                      [$class: 'ChoiceParameter',
                                      choiceType: 'PT_SINGLE_SELECT',
                                      description: 'Select the Environemnt from the Dropdown List',
                                      filterLength: 1,
                                      filterable: false,
                                      name: 'SERVER',
                                      script: [
                                          $class: 'GroovyScript',
                                          fallbackScript: [
                                              classpath: [],
                                              sandbox: false,
                                              script:
                                                  "return['Could not get The environemnts']"
                                          ],
                                          script: [
                                              classpath: [],
                                              sandbox: false,
                                              script:
                                                  "return['silo','stage','prod']"
                                          ]
                                      ]
                                  ],
                      ])
                  ])
                  }
        echo "Starting deployment"
          sshagent(credentials: ['a4d999a5-6318-4659-83be-3f148a5490ca']) {
            sh 'ssh  -o StrictHostKeyChecking=no  voyager@$SERVER.mskcc.org "cd $DIRECTORY && git checkout $BRANCH_NAME && git pull && source run_restart.sh"'
          //sh 'ssh  -o StrictHostKeyChecking=no  voyager@silo.mskcc.org cd /srv/services/staging_voyager/beagle'

          }

        }
      }

  }
}
