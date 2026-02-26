pipeline {
  agent any

  options {
    timestamps()
    ansiColor('xterm')
    disableConcurrentBuilds()
    buildDiscarder(logRotator(numToKeepStr: '30'))
    timeout(time: 45, unit: 'MINUTES')
  }

  parameters {
    booleanParam(name: 'RUN_TERRAFORM_PLAN', defaultValue: true, description: 'Run terraform fmt/validate/plan')
    booleanParam(name: 'RUN_K8S_LINT', defaultValue: true, description: 'Lint Kubernetes manifests with kubeconform')
    choice(name: 'DEPLOY_ENV', choices: ['dev', 'staging', 'prod'], description: 'Target deployment environment')
  }

  environment {
    APP_NAME = 'financial-analytics-api'
    IMAGE_TAG = "${env.BUILD_NUMBER}-${env.GIT_COMMIT?.take(7)}"
    DOCKER_REGISTRY = 'ghcr.io/example-org'
    TERRAFORM_DIR = 'infra/terraform'
    K8S_DIR = 'infra/k8s'
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
        sh 'git --no-pager log -1 --oneline'
      }
    }

    stage('Python Setup') {
      steps {
        sh '''
          python3 -m venv .venv
          . .venv/bin/activate
          pip install --upgrade pip
          pip install -r requirements.txt
        '''
      }
    }

    stage('Unit Tests') {
      steps {
        sh '''
          . .venv/bin/activate
          pytest -q --maxfail=1
        '''
      }
      post {
        always {
          junit testResults: '**/junit*.xml', allowEmptyResults: true
        }
      }
    }

    stage('Build Container') {
      steps {
        sh '''
          docker build -t ${APP_NAME}:${IMAGE_TAG} .
          docker tag ${APP_NAME}:${IMAGE_TAG} ${DOCKER_REGISTRY}/${APP_NAME}:${IMAGE_TAG}
        '''
      }
    }

    stage('Container Security Scan') {
      steps {
        sh '''
          if command -v trivy >/dev/null 2>&1; then
            trivy image --severity HIGH,CRITICAL --exit-code 1 ${APP_NAME}:${IMAGE_TAG}
          else
            echo "trivy not installed; skipping scan"
          fi
        '''
      }
    }

    stage('Terraform Checks') {
      when {
        expression { return params.RUN_TERRAFORM_PLAN }
      }
      steps {
        dir("${TERRAFORM_DIR}") {
          sh '''
            terraform init -backend=false
            terraform fmt -check -recursive
            terraform validate
            terraform plan -var="environment=${DEPLOY_ENV}" -out=tfplan
          '''
        }
      }
    }

    stage('Kubernetes Manifest Checks') {
      when {
        expression { return params.RUN_K8S_LINT }
      }
      steps {
        sh '''
          if command -v kubeconform >/dev/null 2>&1; then
            kubeconform -strict -summary ${K8S_DIR}/*.yaml
          else
            echo "kubeconform not installed; skipping schema validation"
          fi
        '''
      }
    }

    stage('Push Image') {
      when {
        branch 'main'
      }
      steps {
        withCredentials([usernamePassword(credentialsId: 'ghcr-creds', usernameVariable: 'REG_USER', passwordVariable: 'REG_PASS')]) {
          sh '''
            echo "$REG_PASS" | docker login ghcr.io -u "$REG_USER" --password-stdin
            docker push ${DOCKER_REGISTRY}/${APP_NAME}:${IMAGE_TAG}
          '''
        }
      }
    }

    stage('Deploy (Optional)') {
      when {
        allOf {
          branch 'main'
          expression { return params.DEPLOY_ENV != null }
        }
      }
      steps {
        sh '''
          echo "Example deploy stage"
          echo "helm upgrade --install ${APP_NAME} chart/ --set image.tag=${IMAGE_TAG} --namespace ${DEPLOY_ENV}"
        '''
      }
    }
  }

  post {
    success {
      echo "Build succeeded: ${env.JOB_NAME} #${env.BUILD_NUMBER}"
    }
    failure {
      echo "Build failed: ${env.JOB_NAME} #${env.BUILD_NUMBER}"
    }
    cleanup {
      sh 'rm -rf .venv'
    }
  }
}
