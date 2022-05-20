pipeline {
  agent any
/*  parameters {
    choice(name: 'AERVER', choices: ['silo', 'voyager'], description: 'Server')
    string(name: 'DIRECTORY', defaultValue: '/srv/services/beagle_dev/beagle', description: 'Directory')

   } */
  stages {
  stage('Parameters'){
               steps {
                   script {
                   properties([
                           parameters([
                               [$class: 'ChoiceParameter',
                                   choiceType: 'PT_SINGLE_SELECT',
                                   description: 'Select the Environemnt from the Dropdown List',
                                   filterLength: 1,
                                   filterable: false,
                                   name: 'Env',
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
                                               "return['dev','stage']"
                                       ]
                                   ]
                               ],
                               [$class: 'CascadeChoiceParameter',
                                   choiceType: 'PT_SINGLE_SELECT',
                                   description: 'Select the AMI from the Dropdown List',
                                   name: 'AMI List',
                                   referencedParameters: 'Env',
                                   script:
                                       [$class: 'GroovyScript',
                                       fallbackScript: [
                                               classpath: [],
                                               sandbox: false,
                                               script: "return['Could not get Environment from Env Param']"
                                               ],
                                       script: [
                                               classpath: [],
                                               sandbox: false,
                                               script: '''
                                               if (Env.equals("dev")){
                                                   return["ami-sd2345sd", "ami-asdf245sdf", "ami-asdf3245sd"]
                                               }
                                               else if(Env.equals("stage")){
                                                   return["ami-sd34sdf", "ami-sdf345sdc", "ami-sdf34sdf"]
                                               }
                                               else if(Env.equals("prod")){
                                                   return["ami-sdf34sdf", "ami-sdf34ds", "ami-sdf3sf3"]
                                               }
                                               '''
                                           ]
                                   ]
                               ],
                               [$class: 'DynamicReferenceParameter',
                                   choiceType: 'ET_ORDERED_LIST',
                                   description: 'Select the  AMI based on the following information',
                                   name: 'Image Information',
                                   referencedParameters: 'Env',
                                   script:
                                       [$class: 'GroovyScript',
                                       script: 'return["Could not get AMi Information"]',
                                       script: [
                                           script: '''
                                                   if (Env.equals("dev")){
                                                       return["ami-sd2345sd:  AMI with Java", "ami-asdf245sdf: AMI with Python", "ami-asdf3245sd: AMI with Groovy"]
                                                   }
                                                   else if(Env.equals("stage")){
                                                       return["ami-sd34sdf:  AMI with Java", "ami-sdf345sdc: AMI with Python", "ami-sdf34sdf: AMI with Groovy"]
                                                   }
                                                   else if(Env.equals("prod")){
                                                       return["ami-sdf34sdf:  AMI with Java", "ami-sdf34ds: AMI with Python", "ami-sdf3sf3: AMI with Groovy"]
                                                   }
                                                   '''
                                               ]
                                       ]
                               ]
                           ])
                       ])
                   }
               }
           }

    /*  stage("Deploy") {

    steps {

       echo "Starting deployment"
          sshagent(credentials: ['a4d999a5-6318-4659-83be-3f148a5490ca']) {
            sh 'ssh  -o StrictHostKeyChecking=no  voyager@$SERVER.mskcc.org "cd $DIRECTORY && git checkout $BRANCH_NAME && git pull && source run_restart.sh"'
          //sh 'ssh  -o StrictHostKeyChecking=no  voyager@silo.mskcc.org cd /srv/services/staging_voyager/beagle'

          }

        }
      }*/

  }
}
