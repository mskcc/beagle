
pipeline {
  agent any

  stages {
    stage('Logging into Server') {
    steps{
          sshagent(credentials:['fc553c62-8e84-4a2c-b012-db1b9c58195d']){
             sh '''ssh  -o StrictHostKeyChecking=no  pankeyd@silo.mskcc.org uptime'
             whoami '''
             sh 'pwd'
        }
      echo "success login"
       }

   }
 }
}
