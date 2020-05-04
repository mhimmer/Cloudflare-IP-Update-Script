from __future__ import print_function

from requests import get, put
from fcache.cache import FileCache


api_token = "GET-THIS-API-TOKEN-FROM-YOUR-CLOUDFLARE-ACCOUNT"
zone_name = "example.com"
record_names = (
    {"domain": "first", "proxied": True},
    {"domain": "second", "proxied": False},
    {"domain": "thrid", "proxied": False},
)

cf_headers = {
    "Authorization": f"Bearer {api_token}",
    "Content-Type": "application/json"
}
cf_baseurl = "https://api.cloudflare.com/client/v4"

cache = FileCache("cloudflare_update", flag="cs", app_cache_dir="/tmp/cf_updater")


def log(text: str):
    print(text)


def get_my_ip():
    url = "https://api.ipify.org"
    ip_address = ""
    try:
        return get(url).text
    except:
        exit(f"GET {url} failed")
    if ip_address == '':
        exit(f"GET {url} failed")
    return ip_address


def get_zone_id() -> str:
    zone_id = cache.get("zone_id")

    if zone_id is not None:
        return zone_id

    # else
    url = f"{cf_baseurl}/zones?name={zone_name}"
    response = get(url, headers=cf_headers)
    if response.status_code != 200:
        return ""
    response = response.json()

    zone_id = [result.get("id") for result in response.get("result")].pop()
    cache["zone_id"] = zone_id
    return zone_id


def get_record_id(zone_id: str, record_name: str) -> str:
    rec_id = cache.get(f"record_id_{record_name}")

    if rec_id is not None:
        return rec_id

    # else
    url = f"{cf_baseurl}/zones/{zone_id}/dns_records?name={record_name}"
    response = get(url, headers=cf_headers)
    if response.status_code != 200:
        return ""
    response = response.json()

    rec_id = [result.get("id") for result in response.get("result")].pop()
    cache[f"record_id_{record_name}"] = rec_id
    return rec_id


def update_domain_ip(zone_id: str, record_id: str, record_name: str, new_ip: str, proxied: bool = False) -> None:
    url = f"{cf_baseurl}/zones/{zone_id}/dns_records/{record_id}"

    data = {
        "id": zone_id,
        "type": "A",
        "name": record_name,
        "content": new_ip,
        "proxied": proxied,
    }

    response = put(url, json=data, headers=cf_headers)
    if response.status_code != 200:
        log(f"ERROR: Updating {record_name} {response.text}")
        return

    result = response.json()
    result.get("result")
    log(f"DNS record updated: [name: {record_name}, ip: {new_ip}]")


def main():
    current_ip = get_my_ip()
    zone_id = get_zone_id()

    for record in record_names:
        rec_name = record.get("domain")
        rec_name = f"{rec_name}.{zone_name}"
        rec_proxied = record.get("proxied")
        rec_id = get_record_id(zone_id=zone_id, record_name=rec_name)

        last_ip = cache.get(f"last_ip_{rec_name}")
        if last_ip == current_ip:
            log(f"IP has not changed. No update needed. [{rec_name} | {current_ip}]")
            continue
        log(f"IP has changed. [old: {last_ip} | new: {current_ip}]")

        update_domain_ip(
            zone_id=zone_id,
            record_id=rec_id,
            record_name=rec_name,
            new_ip=current_ip,
            proxied=rec_proxied,
        )

        cache[f"last_ip_{rec_name}"] = current_ip


if __name__ == "__main__":
    main()
