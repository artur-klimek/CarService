# CarService Application

## Project Description

CarService is a comprehensive web application for managing a car service business. It provides features for both service employees and customers to manage vehicle repairs, maintenance, and service history.

### Key Features

- **User Management**
  - Role-based access control (Admin, Employee, Customer)
  - Secure authentication and authorization
  - User profile management

- **Vehicle Management**
  - Vehicle registration and tracking
  - Service history
  - Maintenance scheduling
  - Vehicle status monitoring

- **Service Management**
  - Service request creation and tracking
  - Repair and maintenance task management
  - Service status updates
  - Customer notifications

- **Reporting**
  - Service statistics
  - Vehicle history reports
  - Employee performance tracking
  - Financial reports



## Docker Setup (recommended method)

### Building and Running with Docker

1. **Build the Docker image**
   ```bash
   docker build -t carservice:latest .
   ```

2. **Run the container**
   ```bash
   docker run -d \
     --name carservice \
     -p 5000:5000 \
     -v $(pwd)/config.json:/app/config.json \
     -v $(pwd)/logs:/app/logs \
     carservice:latest
   ```

The application will be available at `http://localhost:5000`

### Docker Commands Reference

- **View running container**
  ```bash
  docker ps
  ```

- **View container logs**
  ```bash
  docker logs carservice
  ```

- **Stop the container**
  ```bash
  docker stop carservice
  ```

- **Remove the container**
  ```bash
  docker rm carservice
  ```

- **Remove the image**
  ```bash
  docker rmi carservice:latest
  ```

### Docker Volume Mounts

The container uses two volume mounts:
- `config.json`: For application configuration
- `logs`: For application logs

These volumes ensure that:
- Configuration persists between container restarts
- Logs are accessible from the host system
- Data is not lost when the container is removed


## Local Development Setup

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)
- Git

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/artur-klimek/CarService.git
   cd CarService
   ```

2. **Create and activate virtual environment**
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate

   # Linux/MacOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the database**
   ```bash
   python init_db.py
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

The application will be available at `http://localhost:5000`

### Default Admin Account

After initialization, a default admin account is created:
- Username: admin
- Password: admin123
- Email: admin@carservice.com

**Important**: Change these credentials in production!


## Configuration

The application uses a JSON-based configuration system. The configuration file (`config.json`) is created automatically on first run with default values.


### Configuration Options

#### Logging Configuration
- `level`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `log_dir`: Directory for log files
- `max_log_files`: Maximum number of log files to keep
- `max_log_size_mb`: Maximum size of each log file in MB

#### Server Configuration
- `host`: Server host address
- `port`: Server port number
- `debug`: Debug mode flag (set to false in production)

#### Database Configuration
- `uri`: Database connection URI
- `track_modifications`: SQLAlchemy modification tracking

#### Security Configuration
- `secret_key`: Application secret key (change in production!)
- `session_lifetime`: Session lifetime in seconds

#### Admin Configuration
- `create_default`: Whether to create default admin account
- `username`: Default admin username
- `email`: Default admin email
- `password`: Default admin password

### Environment Variables

The application can also be configured using environment variables:

- `FLASK_APP`: Application entry point (default: app.py)
- `FLASK_ENV`: Environment (development/production)
- `FLASK_DEBUG`: Debug mode (0/1)
- `DATABASE_URI`: Database connection URI
- `SECRET_KEY`: Application secret key

### Production Considerations

1. **Security**
   - Change the default secret key
   - Change default admin credentials
   - Set debug mode to false
   - Use secure database URI
   - Configure proper logging

2. **Performance**
   - Use production-grade database (PostgreSQL recommended)
   - Configure proper logging rotation
   - Set appropriate session lifetime
   - Use production-grade web server (e.g., Gunicorn)

3. **Monitoring**
   - Configure appropriate log levels
   - Set up log rotation
   - Monitor database connections
   - Track application metrics

## Development

### Project Structure

```
CarService/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── forms.py
│   ├── models.py
│   ├── routes/
│   ├── static/
│   ├── templates/
│   └── utils/
├── logs/
├── tests/
├── app.py
├── config.json
├── requirements.txt
└── README.md
```


## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 