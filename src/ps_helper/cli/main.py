import json
import os
import subprocess
import click
from ..scripts.generate_report import generate_html_report

TEMPLATE_REPO = "https://github.com/bitmakerla/scrapy_template.git"


@click.group()
def main():
    """PS Helper CLI"""
    click.echo("🚀 PS Helper CLI is running!")


@main.command()
@click.argument("project_name")
def create_repo_template(project_name):
    """Create a new project from the template repo"""
    click.echo(f"Creating project '{project_name}' from template...")

    if os.path.exists(project_name):
        click.echo(f"❌ Directory '{project_name}' already exists.")
        return

    try:
        subprocess.run(["git", "clone", TEMPLATE_REPO, project_name], check=True)
        # remove .git so it's a clean project
        git_dir = os.path.join(project_name, ".git")
        subprocess.run(["rm", "-rf", git_dir], check=True)
        click.echo(f"✅ Project '{project_name}' created successfully!")
    except subprocess.CalledProcessError as e:
        click.echo(f"❌ Error cloning template: {e}")


@main.command()
@click.argument("metrics_path", type=click.Path(exists=True))
def create_report(metrics_path):
    """Generate HTML report from Scrapy metrics JSON file"""
    click.echo(f"📊 Generating report from '{metrics_path}'...")

    try:
        report_path = generate_html_report(metrics_path)
        click.echo(f"✅ Report generated successfully: {report_path}")

    except FileNotFoundError:
        click.echo(f"❌ File '{metrics_path}' not found")
    except json.JSONDecodeError:
        click.echo(f"❌ Invalid JSON file: '{metrics_path}'")
    except Exception as e:
        click.echo(f"❌ Error generating report: {e}")
