pipeline {
  agent any

  triggers {
    githubPush() // Enabling being build on Push
  }
  stages {
    stage("SSH Steps") {
      steps {
        sshagent(credentials: ['a4d999a5-6318-4659-83be-3f148a5490ca']) {
          sh 'ssh  -o StrictHostKeyChecking=no  voyager@silo.mskcc.org "cd /srv/services/staging_voyager/beagle && git checkout develop"'
        //sh 'ssh  -o StrictHostKeyChecking=no  voyager@silo.mskcc.org cd /srv/services/staging_voyager/beagle'

        }

      }
    }
  }
}
//trigger build
