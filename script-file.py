import os
import json
import subprocess
import requests
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

PACKAGIST_API_LIST = "https://packagist.org/packages/list.json"
PACKAGIST_API_PACKAGE = "https://packagist.org/packages/{vendor}/{package}.json"
CLONE_DIR = "/app/repos"
REPORT_DIR = "/app/reports"

os.makedirs(CLONE_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

def get_all_packages():
    response = requests.get(PACKAGIST_API_LIST)
    response.raise_for_status()
    return response.json()["packageNames"]


def get_repo_url(package_name):
    vendor, package = package_name.split("/", 1)
    response = requests.get(PACKAGIST_API_PACKAGE.format(vendor=vendor, package=package))
    
    if response.status_code == 200:
        data = response.json()
        return data.get("package", {}).get("repository")
    return None


def clone_repo(repo_url, local_path):
    if os.path.exists(local_path):
        return True
    
    result = subprocess.run(["git", "clone", "--depth=1", repo_url, local_path], capture_output=True, text=True)
    
    return result.returncode == 0


def run_phpmetrics(project_path):
    result = subprocess.run(
        ["phpmetrics", project_path],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        return None

    output = result.stdout
    
    metrics = {
        'loc': extract_metric(output, 'Lines of code'),
        'lloc': extract_metric(output, 'Logical lines of code'),
        'lloc_class': extract_metric(output, 'Logical lines of code by class'),
        'lloc_method': extract_metric(output, 'Logical lines of code by method'),
        'classes': extract_metric(output, 'Classes'),
        'methods': extract_metric(output, 'Methods'),
        'methods_by_class': extract_metric(output, 'Methods by class'),
        'lcm': extract_metric(output, 'Lack of cohesion of methods'),
        'aci': extract_metric(output, 'Average afferent coupling'),
        'eco': extract_metric(output, 'Average efferent coupling'),
        'ai': extract_metric(output, 'Average instability'),
        'dit': extract_metric(output, 'Depth of Inheritance Tree'),
        'cc': extract_metric(output, 'Average Cyclomatic complexity by class'),
        'wmc': extract_metric(output, 'Average Weighted method count by class'),
        'rcs': extract_metric(output, 'Average Relative system complexity'),
        'ad': extract_metric(output, 'Average Difficulty'),
        'abc': extract_metric(output, 'Average bugs by class'),
        'kloc': extract_metric(output, 'Average defects by class \(Kan\)')
    }
    
    return metrics


def extract_metric(output, metric_name):
    import re
    match = re.search(rf"{metric_name}\s+([\d.]+)", output)
    return float(match.group(1)) if match else None


def delete_repo(local_path):
    if os.path.exists(local_path):
        for root, dirs, files in os.walk(local_path, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(local_path)


def process_package(package, results, output_file):

    repo_url = get_repo_url(package)
    if not repo_url:
        return None

    local_path = os.path.join(CLONE_DIR, package.replace("/", "_"))

    if clone_repo(repo_url, local_path):
        metrics = run_phpmetrics(local_path)
        if metrics:
            results[package] = metrics
        
        delete_repo(local_path)

        with open(output_file, "w") as f:
            json.dump(results, f, indent=None, separators=(',', ':'))


def main():
    packages = get_all_packages()
    results = {}
    output_file = os.path.join(REPORT_DIR, "phpmetrics_summary.json")
    
    with ThreadPoolExecutor(max_workers=12) as executor:  
        futures = {executor.submit(process_package, package, results, output_file): package for package in packages[:100]}  
        for future in tqdm(as_completed(futures), total=len(futures)):
            future.result()  

    print("done")

if __name__ == "__main__":
    main()