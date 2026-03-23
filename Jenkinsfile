pipeline {
    agent any

    stages {

        stage('Clonar repositorio') {
            steps {
                git branch: 'main',
                    url: 'https://github.com/CristianMurguia/AppEncuestas.git'
            }
        }

        stage('Instalar dependencias') {
            steps {
                bat 'python -m pip install django'
            }
        }

        stage('Verificar errores Django') {
            steps {
                bat 'python manage.py check'
            }
        }

        stage('Correr tests') {
            steps {
                bat 'python manage.py test surveys --verbosity=2'
            }
        }

    }

    post {
        success {
            echo 'Todo OK - Sin errores'
        }
        failure {
            echo 'FALLO - Revisa los errores arriba'
        }
    }
}