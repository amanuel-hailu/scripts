import { execSync } from "child_process";
import fs from "fs";
import * as path from "path";

// Repository SSH URL and local path where you want to clone the repository
const repoSSH = "git@github.com:MedStarSiTEL/lms-core.git";
const clonePath = "./localRepositoryPath"; // Ensure this path is where you want to clone the repo

// Function to clone repository if it's not already cloned
function cloneRepository() {
  try {
    if (!fs.existsSync(clonePath)) {
      console.log(`Cloning repository to ${clonePath}`);
      execSync(`git clone ${repoSSH} ${clonePath}`);
      console.log("Repository cloned successfully.");
    } else {
      console.log(`Repository already exists at ${clonePath}`);
    }
  } catch (error) {
    console.error(
      `Failed to clone the repository: ${(error as Error).message}`
    );
    process.exit(1); // Exit the script with an error code
  }
}

// Function to get a list of all contributors
function getContributors() {
  try {
    console.log("Fetching contributors...");
    const contributorsString = execSync('git log --format="%aN" | sort -u', {
      cwd: clonePath,
    }).toString();
    const contributors = contributorsString.split("\n").filter(Boolean); // Split by new line and remove empty lines
    console.log("Contributors fetched successfully.");
    return contributors;
  } catch (error) {
    console.error(`Failed to fetch contributors: ${(error as Error).message}`);
    return []; // Return an empty array to allow the script to continue
  }
}

// Function to get a list of all branches
function getBranches() {
  try {
    console.log("Fetching branches...");
    const branchesString = execSync("git branch -r", {
      cwd: clonePath,
    }).toString();
    const branches = branchesString
      .split("\n")
      .map((branch) => branch.trim().replace("origin/", ""))
      .filter(Boolean);
    console.log("Branches fetched successfully.");
    return branches;
  } catch (error) {
    console.error(`Failed to fetch branches: ${(error as Error).message}`);
    return []; // Return an empty array to allow the script to continue
  }
}

// Main function to generate the report
async function generateReport() {
  try {
    console.log("Starting report generation...");

    // Ensure the clonePath directory exists
    if (!fs.existsSync(clonePath)) {
      console.log(`Creating directory at ${clonePath}`);
      fs.mkdirSync(clonePath, { recursive: true });
      console.log("Directory created successfully.");
    }

    cloneRepository(); // Ensure the repository is cloned

    // Change directory to the cloned repository for subsequent commands
    process.chdir(clonePath);

    const contributors = getContributors();
    const branches = getBranches();

    let report: { [key: string]: string[] } = {}; // Specify the type of report

    // Initialize report structure
    contributors.forEach((contributor) => {
      report[contributor] = [];
    });

    // Simplified logic for associating branches with contributors
    console.log("Generating report...");
    console.log("Contributors:", contributors);
    console.log("Branches:", branches);

    console.log("Report generation complete.");
  } catch (error) {
    console.error(
      `An error occurred during report generation: ${(error as Error).message}`
    );
    process.exit(1); // Exit the script with an error code
  }
}

generateReport();
