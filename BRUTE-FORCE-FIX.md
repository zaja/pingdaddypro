# PingDaddyPro Brute Force Protection Fix

## Problem

Brute force zaštita za prijavu korisnika u PingDaddyPro aplikaciju nije radila jer aplikacija nije pravilno detektirala IP adresu korisnika kada se pokreće u Docker okruženju iza reverse proxy-a.

### Uzrok problema

1. **Pogrešno dobivanje IP adrese**: Aplikacija je koristila `request.remote_addr` koji u Docker okruženju vraća IP adresu Docker kontejnera umjesto stvarne IP adrese korisnika.

2. **Nedostatak X-Forwarded-For podrške**: Aplikacija nije koristila `X-Forwarded-For` header koji nginx reverse proxy postavlja s pravom IP adresom korisnika.

3. **Nedostatak validacije IP adresa**: Nije bilo validacije IP adresa što može dovesti do sigurnosnih problema.

## Rješenje

### 1. Dodana nova funkcija za dobivanje IP adrese

```python
def get_client_ip():
    """Get the real client IP address, handling reverse proxy setups"""
    # Check for X-Forwarded-For header first (for reverse proxy setups)
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs, take the first one (original client)
        ip_address = forwarded_for.split(',')[0].strip()
        if ip_address and is_valid_ip(ip_address):
            return ip_address
    
    # Check for X-Real-IP header (alternative header used by some proxies)
    real_ip = request.headers.get('X-Real-IP')
    if real_ip and is_valid_ip(real_ip.strip()):
        return real_ip.strip()
    
    # Fallback to request.remote_addr
    return request.remote_addr
```

### 2. Dodana validacija IP adresa

```python
def is_valid_ip(ip_address):
    """Validate if the given string is a valid IP address"""
    import socket
    try:
        # Try to parse as IPv4 or IPv6
        socket.inet_aton(ip_address)
        return True
    except socket.error:
        try:
            socket.inet_pton(socket.AF_INET6, ip_address)
            return True
        except socket.error:
            return False
```

### 3. Ažuriran login endpoint

```python
@app.route('/api/login', methods=['POST'])
def api_login():
    # Get real client IP address
    ip_address = get_client_ip()
    
    print(f"DEBUG LOGIN: Username={username}, IP={ip_address}")
    # ... rest of the login logic
```

### 4. Poboljšana sigurnost

- Dodana validacija IP adresa u svim funkcijama koje rade s IP adresama
- Poboljšan logging za sigurnosne događaje
- Dodana cleanup funkcija za stare login pokušaje
- Dodan API endpoint za resetiranje brute force lockout-a

### 5. Dodana cleanup funkcija

```python
# Clean up old login attempts (keep only last 30 days for security monitoring)
login_cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
cursor.execute('DELETE FROM login_attempts WHERE attempt_time < %s', (login_cutoff_date,))
```

## Testiranje

Kreiran je test script `test_brute_force.py` koji testira brute force zaštitu:

```bash
python test_brute_force.py http://localhost:5000
```

Script testira:
1. Inicijalni status autentifikacije
2. Višestruke neuspješne prijave
3. Pokušaj prijave s ispravnim lozinkom nakon lockout-a
4. Testiranje s različitim IP adresama

## Konfiguracija nginx-a

Nginx je već konfiguriran da postavlja potrebne headere:

```nginx
location / {
    proxy_pass http://pingdaddypro;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

## Sigurnosne značajke

### Brute Force Zaštita

1. **Korisnički lockout**: Nakon 4 neuspješna pokušaja, korisnički račun se zaključava na 15 minuta
2. **IP lockout**: Nakon 10 neuspješnih pokušaja s iste IP adrese u 15 minuta, IP se zaključava
3. **Automatsko otključavanje**: Lockout se automatski poništava nakon 15 minuta
4. **Validacija IP adresa**: Sve IP adrese se validiraju prije korištenja
5. **Sigurnosno logiranje**: Svi pokušaji prijave se logiraju za sigurnosni nadzor

### API Endpoints

- `POST /api/reset-brute-force` - Resetiranje brute force lockout-a (zahtijeva autentifikaciju)

## Deployment

Nakon primjene ovih izmjena:

1. Restartajte Docker kontejnere:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

2. Testirajte brute force zaštitu:
   ```bash
   python test_brute_force.py
   ```

3. Provjerite logove:
   ```bash
   docker logs pingdaddypro
   ```

## Monitoring

Za praćenje sigurnosnih događaja, pratite logove aplikacije:

```bash
# Praćenje svih logova
docker logs -f pingdaddypro

# Filtriranje sigurnosnih događaja
docker logs pingdaddypro | grep "SECURITY LOG"
```

## Troubleshooting

### Problem: Brute force zaštita i dalje ne radi

1. Provjerite da li su X-Forwarded-For headeri postavljeni:
   ```bash
   curl -H "X-Forwarded-For: 192.168.1.100" http://localhost:5000/api/auth-status
   ```

2. Provjerite Docker logove:
   ```bash
   docker logs pingdaddypro | grep "DEBUG LOGIN"
   ```

3. Provjerite bazu podataka:
   ```bash
   docker exec -it pingdaddypro-postgres psql -U pingdaddypro -d pingdaddypro
   SELECT * FROM login_attempts ORDER BY attempt_time DESC LIMIT 10;
   ```

### Problem: IP adrese se ne detektiraju

1. Provjerite nginx konfiguraciju
2. Provjerite da li se aplikacija pokreće iza reverse proxy-a
3. Testirajte s direktnim pristupom na port 5000

## Sigurnosne preporuke

1. **Promijenite zadanu lozinku** odmah nakon prve prijave
2. **Koristite jaku lozinku** (najmanje 12 znakova, kombinacija slova, brojeva i simbola)
3. **Pratite logove** za sumnjive aktivnosti
4. **Redovito ažurirajte** aplikaciju
5. **Koristite HTTPS** u produkciji
6. **Ograničite pristup** na firewall razini ako je moguće
