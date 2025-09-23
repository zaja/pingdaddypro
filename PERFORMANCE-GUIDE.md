# 📊 Ping Daddy Pro v1.0.3 - Performance Guide

## 🎯 Overview

This guide explains data generation patterns, PostgreSQL performance characteristics, and system requirements for Ping Daddy Pro at different monitoring scales.

## 📈 Data Generation Patterns

### **Monitoring Scenarios**

| Scenario | Websites | Interval | Daily Checks | Monthly Data | Yearly Data |
|----------|----------|----------|--------------|--------------|-------------|
| **Small** | 2 sites | 5 min | 576 checks | 17,280 records | 207,360 records |
| **Medium** | 5 sites | 2 min | 7,200 checks | 216,000 records | 2,592,000 records |
| **Large** | 10 sites | 1 min | 14,400 checks | 432,000 records | 5,184,000 records |
| **Enterprise** | 50 sites | 30 sec | 172,800 checks | 5,184,000 records | 62,208,000 records |

### **Data Structure Per Check**

Each monitoring check generates:
- **1 record** in `monitoring_history` table
- **1 record** in `ssl_certificates` table (if SSL monitoring enabled)
- **1 record** in `performance_metrics` table (if performance monitoring enabled)

**Total records per check:** 1-3 records depending on enabled features.

## 🗄️ PostgreSQL Database Performance

### **Table Sizes (Estimated)**

| Table | Small (2 sites) | Medium (5 sites) | Large (10 sites) | Enterprise (50 sites) |
|-------|-----------------|------------------|------------------|----------------------|
| `monitoring_history` | 207K records | 2.6M records | 5.2M records | 62M records |
| `ssl_certificates` | 207K records | 2.6M records | 5.2M records | 62M records |
| `performance_metrics` | 207K records | 2.6M records | 5.2M records | 62M records |
| **Total Records** | **621K** | **7.8M** | **15.6M** | **186M** |

### **Storage Requirements**

| Scenario | Daily Growth | Monthly Growth | Yearly Growth | 5-Year Growth |
|----------|--------------|----------------|---------------|---------------|
| **Small** | ~2 MB | ~60 MB | ~720 MB | ~3.6 GB |
| **Medium** | ~25 MB | ~750 MB | ~9 GB | ~45 GB |
| **Large** | ~50 MB | ~1.5 GB | ~18 GB | ~90 GB |
| **Enterprise** | ~250 MB | ~7.5 GB | ~90 GB | ~450 GB |

## ⚡ PostgreSQL Performance Characteristics

### **Query Performance**

PostgreSQL handles Ping Daddy Pro workloads excellently:

#### **✅ Strengths:**
- **Indexed Queries** - All queries use proper indexes
- **Efficient Joins** - Optimized table relationships
- **Connection Pooling** - psycopg2 connection management
- **Memory Management** - Automatic query optimization
- **Concurrent Access** - Multiple users without performance impact

#### **📊 Query Types & Performance:**

| Query Type | Frequency | Performance | Index Usage |
|------------|-----------|-------------|-------------|
| **INSERT** (new checks) | Every 1-30 seconds | **Excellent** | Primary keys |
| **SELECT** (dashboard) | Every 5-10 seconds | **Excellent** | Composite indexes |
| **UPDATE** (status changes) | Occasional | **Excellent** | Primary keys |
| **DELETE** (cleanup) | Daily | **Good** | Date indexes |
| **Aggregate** (statistics) | On-demand | **Good** | Date + status indexes |

### **Database Optimization Features**

#### **🔧 Built-in Optimizations:**
- **Composite Indexes** on `(website_id, check_time)`
- **Date-based Partitioning** for large datasets
- **Automatic VACUUM** for maintenance
- **Query Plan Optimization** by PostgreSQL
- **Connection Pooling** with psycopg2

#### **📈 Performance Scaling:**

| Concurrent Users | Response Time | Database Load | Memory Usage |
|------------------|---------------|---------------|--------------|
| **1-5 users** | <100ms | Low | <100MB |
| **5-20 users** | <200ms | Medium | <200MB |
| **20-50 users** | <500ms | High | <500MB |
| **50+ users** | <1000ms | Very High | <1GB |

## 🚀 System Requirements

### **Minimum Requirements**

| Component | Small | Medium | Large | Enterprise |
|-----------|-------|--------|-------|------------|
| **CPU** | 1 core | 2 cores | 4 cores | 8+ cores |
| **RAM** | 1GB | 2GB | 4GB | 8GB+ |
| **Storage** | 5GB | 20GB | 50GB | 200GB+ |
| **Network** | 10Mbps | 50Mbps | 100Mbps | 1Gbps+ |

### **Recommended Requirements**

| Component | Small | Medium | Large | Enterprise |
|-----------|-------|--------|-------|------------|
| **CPU** | 2 cores | 4 cores | 8 cores | 16+ cores |
| **RAM** | 2GB | 4GB | 8GB | 16GB+ |
| **Storage** | 20GB | 100GB | 500GB | 2TB+ |
| **Network** | 50Mbps | 100Mbps | 1Gbps | 10Gbps+ |

## 🔧 Performance Tuning

### **PostgreSQL Configuration**

#### **Recommended Settings:**
```sql
-- Memory settings
shared_buffers = 256MB          -- 25% of RAM
effective_cache_size = 1GB      -- 75% of RAM
work_mem = 4MB                  -- Per query memory
maintenance_work_mem = 64MB     -- Maintenance operations

-- Connection settings
max_connections = 100           -- Concurrent connections
shared_preload_libraries = 'pg_stat_statements'

-- Logging
log_min_duration_statement = 1000  -- Log slow queries
log_checkpoints = on
log_connections = on
log_disconnections = on
```

#### **Index Optimization:**
```sql
-- Create additional indexes for large datasets
CREATE INDEX CONCURRENTLY idx_monitoring_history_website_time 
ON monitoring_history(website_id, check_time DESC);

CREATE INDEX CONCURRENTLY idx_monitoring_history_status_time 
ON monitoring_history(status, check_time DESC);

CREATE INDEX CONCURRENTLY idx_ssl_certificates_expiry 
ON ssl_certificates(expiry_date);
```

### **Application-Level Optimizations**

#### **Connection Pooling:**
```python
# In pingdaddypro.py
import psycopg2.pool

# Create connection pool
connection_pool = psycopg2.pool.ThreadedConnectionPool(
    minconn=1,
    maxconn=20,
    dsn=DATABASE_URL
)
```

#### **Batch Operations:**
```python
# Batch insert for better performance
def batch_insert_history(records):
    cursor = get_db_cursor()
    cursor.executemany(
        "INSERT INTO monitoring_history (website_id, check_time, status, response_time) VALUES (%s, %s, %s, %s)",
        records
    )
    cursor.connection.commit()
```

## 📊 Monitoring Performance

### **Real-time Monitoring**

#### **Dashboard Performance:**
- **Page Load Time:** <2 seconds
- **Data Refresh:** Every 5 seconds
- **Chart Rendering:** <1 second
- **API Response:** <500ms

#### **Background Monitoring:**
- **Check Interval:** 1-30 seconds (configurable)
- **Concurrent Checks:** Up to 50 websites
- **Memory Usage:** <100MB per 10 websites
- **CPU Usage:** <10% per 10 websites

### **Data Retention Policies**

#### **Recommended Retention:**
```sql
-- Keep detailed data for 30 days
DELETE FROM monitoring_history 
WHERE check_time < NOW() - INTERVAL '30 days';

-- Keep aggregated data for 1 year
DELETE FROM performance_metrics 
WHERE check_time < NOW() - INTERVAL '1 year';

-- Keep SSL data for 1 year
DELETE FROM ssl_certificates 
WHERE expiry_date < NOW() - INTERVAL '1 year';
```

## 🚨 Performance Alerts

### **Warning Thresholds**

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| **Response Time** | >2 seconds | >5 seconds | Check network |
| **Database Size** | >10GB | >50GB | Cleanup old data |
| **Memory Usage** | >80% | >95% | Restart container |
| **CPU Usage** | >70% | >90% | Scale resources |
| **Disk Space** | >80% | >95% | Add storage |

### **Monitoring Commands**

```bash
# Check database size
docker exec pingdaddypro-db psql -U pingdaddypro -d pingdaddypro -c "
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"

# Check query performance
docker exec pingdaddypro-db psql -U pingdaddypro -d pingdaddypro -c "
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;"

# Check connection count
docker exec pingdaddypro-db psql -U pingdaddypro -d pingdaddypro -c "
SELECT count(*) as active_connections 
FROM pg_stat_activity 
WHERE state = 'active';"
```

## 📈 Scaling Recommendations

### **Horizontal Scaling**

#### **Load Balancer Setup:**
```yaml
# docker-compose.scale.yml
version: '3.8'
services:
  pingdaddypro-app:
    image: svejedobro/pingdaddypro:latest
    deploy:
      replicas: 3
    environment:
      - DATABASE_URL=postgresql://pingdaddypro:pingdaddypro@db:5432/pingdaddypro
    depends_on:
      - db
  
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - pingdaddypro-app
```

#### **Database Clustering:**
```yaml
# docker-compose.cluster.yml
version: '3.8'
services:
  db-primary:
    image: postgres:15
    environment:
      - POSTGRES_DB=pingdaddypro
      - POSTGRES_USER=pingdaddypro
      - POSTGRES_PASSWORD=pingdaddypro
    volumes:
      - postgres_primary:/var/lib/postgresql/data
  
  db-replica:
    image: postgres:15
    environment:
      - POSTGRES_DB=pingdaddypro
      - POSTGRES_USER=pingdaddypro
      - POSTGRES_PASSWORD=pingdaddypro
    volumes:
      - postgres_replica:/var/lib/postgresql/data
```

### **Vertical Scaling**

#### **Resource Allocation:**
```yaml
# docker-compose.production.yml
version: '3.8'
services:
  pingdaddypro-app:
    image: svejedobro/pingdaddypro:latest
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 8G
        reservations:
          cpus: '2.0'
          memory: 4G
  
  db:
    image: postgres:15
    deploy:
      resources:
        limits:
          cpus: '8.0'
          memory: 16G
        reservations:
          cpus: '4.0'
          memory: 8G
```

## 🔍 Troubleshooting

### **Common Performance Issues**

#### **Slow Dashboard Loading:**
```bash
# Check database performance
docker exec pingdaddypro-db psql -U pingdaddypro -d pingdaddypro -c "
EXPLAIN ANALYZE 
SELECT * FROM monitoring_history 
WHERE website_id = 1 
ORDER BY check_time DESC 
LIMIT 100;"
```

#### **High Memory Usage:**
```bash
# Check container resources
docker stats pingdaddypro-app pingdaddypro-db

# Restart if needed
docker restart pingdaddypro-app
```

#### **Database Connection Issues:**
```bash
# Check connection pool
docker exec pingdaddypro-app python -c "
import psycopg2
conn = psycopg2.connect('postgresql://pingdaddypro:pingdaddypro@db:5432/pingdaddypro')
print('Connection successful')
conn.close()
"
```

## 📚 Additional Resources

### **PostgreSQL Documentation:**
- [PostgreSQL Performance Tuning](https://www.postgresql.org/docs/current/performance-tips.html)
- [PostgreSQL Indexing](https://www.postgresql.org/docs/current/indexes.html)
- [PostgreSQL Monitoring](https://www.postgresql.org/docs/current/monitoring.html)

### **Docker Performance:**
- [Docker Resource Management](https://docs.docker.com/config/containers/resource_constraints/)
- [Docker Compose Scaling](https://docs.docker.com/compose/reference/up/#scale)

### **Monitoring Tools:**
- [pgAdmin](https://www.pgadmin.org/) - PostgreSQL administration
- [Grafana](https://grafana.com/) - Performance dashboards
- [Prometheus](https://prometheus.io/) - Metrics collection

---

**💡 Tip:** Start with small monitoring loads and gradually scale up. Monitor performance metrics and adjust resources as needed.

**🔧 Support:** For performance issues, check the logs and use the troubleshooting commands above.
