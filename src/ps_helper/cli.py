import os
import subprocess
import click

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
        subprocess.run(
            ["git", "clone", TEMPLATE_REPO, project_name],
            check=True
        )
        # remove .git so it's a clean project
        git_dir = os.path.join(project_name, ".git")
        subprocess.run(["rm", "-rf", git_dir], check=True)
        click.echo(f"✅ Project '{project_name}' created successfully!")
    except subprocess.CalledProcessError as e:
        click.echo(f"❌ Error cloning template: {e}")
