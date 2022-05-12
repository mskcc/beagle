pipeline {
  agent any

  triggers {
    pollSCM('') // Enabling being build on Push
  }
  stages {
    stage("SSH Steps") {
      steps {
        sshagent(credentials: ['fc553c62-8e84-4a2c-b012-db1b9c58195d']) {
          sh 'ssh  -o StrictHostKeyChecking=no  pankeyd@silo.mskcc.org "cd /srv/services/staging_voyager/beagle && git checkout develop"'

        }

      }
    }
  }
}
