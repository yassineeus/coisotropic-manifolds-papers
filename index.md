import os
import datetime

def generate_index_md():
    """Generates the index.md file with the current date"""
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Check if the database CSV file exists
    if not os.path.exists("coisotropic_manifolds_database.csv"):
        print("Warning: The file coisotropic_manifolds_database.csv does not exist.")
    
    # Content of the index.md file
    index_content = f"""---
layout: default
title: Coisotropic Manifolds - Database
---

# Coisotropic Manifolds Database

*Updated: {current_date}*

This page presents a collection of scientific articles on coisotropic manifolds and related topics, collected from arXiv (1975-present).

<div class="stats-container">
  <div class="stat-box">
    <span class="stat-number" id="totalArticles">-</span>
    <span class="stat-label">Total articles</span>
  </div>
  <div class="stat-box">
    <span class="stat-number" id="decades">-</span>
    <span class="stat-label">Decades covered</span>
  </div>
  <div class="stat-box">
    <span class="stat-number" id="categories">-</span>
    <span class="stat-label">Categories</span>
  </div>
</div>

## Search the database

<div class="search-container">
  <input type="text" id="searchInput" onkeyup="searchArticles()" placeholder="Search by title, author, category...">
  <div class="filter-container">
    <select id="yearFilter" onchange="applyFilters()">
      <option value="">All years</option>
    </select>
    <select id="categoryFilter" onchange="applyFilters()">
      <option value="">All categories</option>
    </select>
  </div>
</div>

<div id="loadingIndicator" style="display:none;">Loading data...</div>
<div id="searchResults"></div>

## Publication trends

<div id="yearlyChart" class="chart-container">
  <canvas id="publicationsChart"></canvas>
</div>

## Recent articles

<table id="recentArticlesTable">
  <thead>
    <tr>
      <th>Date</th>
      <th>Authors</th>
      <th>Title</th>
      <th>Categories</th>
      <th>Link</th>
    </tr>
  </thead>
  <tbody id="recentArticles">
    <tr>
      <td colspan="5" class="loading-message">Loading recent articles...</td>
    </tr>
  </tbody>
</table>

## Top authors

<div id="authorsChart" class="chart-container">
  <canvas id="topAuthorsChart"></canvas>
</div>

## Download data

<div class="download-buttons">
  <a href="coisotropic_manifolds_database.csv" class="download-button" download>Download full database (CSV)</a>
  <a href="https://github.com/your-username/coisotropic-manifolds" class="download-button">Source code on GitHub</a>
</div>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script src="https://cdn.jsdelivr.net/npm/papaparse@5.3.0/papaparse.min.js"></script>

<script>
// Global variables
let articlesData = [];
let yearlyData = {};
let categoryData = {};
let authorData = {};
let publicationsChart = null;
let authorsChart = null;

// Function to load and process CSV data
function loadData() {
  document.getElementById('loadingIndicator').style.display = 'block';
  
  Papa.parse('coisotropic_manifolds_database.csv', {
    download: true,
    header: true,
    complete: function(results) {
      articlesData = results.data.filter(row => row.title && row.published_date);
      processData(articlesData);
      updateUI();
      document.getElementById('loadingIndicator').style.display = 'none';
    },
    error: function(error) {
      console.error('Error loading data:', error);
      document.getElementById('loadingIndicator').style.display = 'none';
      document.getElementById('searchResults').innerHTML = '<p class="error-message">Error loading data. Please try again later.</p>';
    }
  });
}

// Process data for statistics and charts
function processData(data) {
  // Extract years
  yearlyData = {};
  data.forEach(article => {
    if (article.published_date) {
      const year = article.published_date.substring(0, 4);
      yearlyData[year] = (yearlyData[year] || 0) + 1;
    }
  });
  
  // Extract categories
  categoryData = {};
  data.forEach(article => {
    if (article.categories) {
      const cats = article.categories.split(',');
      cats.forEach(cat => {
        const trimmedCat = cat.trim();
        if (trimmedCat) {
          categoryData[trimmedCat] = (categoryData[trimmedCat] || 0) + 1;
        }
      });
    }
  });
  
  // Extract authors
  authorData = {};
  data.forEach(article => {
    if (article.authors) {
      const authors = article.authors.split(',');
      authors.forEach(author => {
        const trimmedAuthor = author.trim();
        if (trimmedAuthor) {
          authorData[trimmedAuthor] = (authorData[trimmedAuthor] || 0) + 1;
        }
      });
    }
  });
  
  // Fill year filters
  const yearSelect = document.getElementById('yearFilter');
  const years = Object.keys(yearlyData).sort().reverse();
  yearSelect.innerHTML = '<option value="">All years</option>';
  years.forEach(year => {
    const option = document.createElement('option');
    option.value = year;
    option.textContent = year;
    yearSelect.appendChild(option);
  });
  
  // Fill category filters
  const categorySelect = document.getElementById('categoryFilter');
  const categories = Object.keys(categoryData).sort();
  categorySelect.innerHTML = '<option value="">All categories</option>';
  categories.forEach(category => {
    const option = document.createElement('option');
    option.value = category;
    option.textContent = category;
    categorySelect.appendChild(option);
  });
}

// Update user interface
function updateUI() {
  // Update statistics
  document.getElementById('totalArticles').textContent = articlesData.length;
  
  // Calculate number of decades covered
  const years = Object.keys(yearlyData).map(y => parseInt(y));
  const minYear = Math.min(...years);
  const maxYear = Math.max(...years);
  const decades = Math.floor((maxYear - minYear) / 10) + 1;
  document.getElementById('decades').textContent = decades;
  
  // Number of categories
  document.getElementById('categories').textContent = Object.keys(categoryData).length;
  
  // Display recent articles
  displayRecentArticles();
  
  // Create charts
  createYearlyChart();
  createAuthorsChart();
}

// Display recent articles
function displayRecentArticles() {
  const tbody = document.getElementById('recentArticles');
  const recentArticles = [...articlesData]
    .sort((a, b) => b.published_date.localeCompare(a.published_date))
    .slice(0, 10);
  
  if (recentArticles.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5">No articles found</td></tr>';
    return;
  }
  
  tbody.innerHTML = '';
  recentArticles.forEach(article => {
    const row = document.createElement('tr');
    
    const dateCell = document.createElement('td');
    dateCell.textContent = article.published_date;
    
    const authorsCell = document.createElement('td');
    authorsCell.textContent = article.authors;
    
    const titleCell = document.createElement('td');
    titleCell.textContent = article.title;
    
    const categoriesCell = document.createElement('td');
    categoriesCell.textContent = article.categories;
    
    const linkCell = document.createElement('td');
    const link = document.createElement('a');
    link.href = article.url;
    link.textContent = `arXiv:${article.id}`;
    link.target = '_blank';
    linkCell.appendChild(link);
    
    row.appendChild(dateCell);
    row.appendChild(authorsCell);
    row.appendChild(titleCell);
    row.appendChild(categoriesCell);
    row.appendChild(linkCell);
    
    tbody.appendChild(row);
  });
}

// Create yearly publications chart
function createYearlyChart() {
  const ctx = document.getElementById('publicationsChart').getContext('2d');
  
  // Sort years and prepare data
  const sortedYears = Object.keys(yearlyData).sort();
  const counts = sortedYears.map(year => yearlyData[year]);
  
  // If a chart already exists, destroy it
  if (publicationsChart) {
    publicationsChart.destroy();
  }
  
  // Create new chart
  publicationsChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: sortedYears,
      datasets: [{
        label: 'Number of publications',
        data: counts,
        backgroundColor: 'rgba(54, 162, 235, 0.6)',
        borderColor: 'rgba(54, 162, 235, 1)',
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'Number of articles'
          }
        },
        x: {
          title: {
            display: true,
            text: 'Year'
          }
        }
      },
      plugins: {
        title: {
          display: true,
          text: 'Publications by year'
        }
      }
    }
  });
}

// Create top authors chart
function createAuthorsChart() {
  const ctx = document.getElementById('topAuthorsChart').getContext('2d');
  
  // Sort authors by number of publications
  const sortedAuthors = Object.entries(authorData)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10);
  
  const authorNames = sortedAuthors.map(entry => entry[0]);
  const authorCounts = sortedAuthors.map(entry => entry[1]);
  
  // If a chart already exists, destroy it
  if (authorsChart) {
    authorsChart.destroy();
  }
  
  // Create new chart
  authorsChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: authorNames,
      datasets: [{
        label: 'Number of publications',
        data: authorCounts,
        backgroundColor: 'rgba(75, 192, 192, 0.6)',
        borderColor: 'rgba(75, 192, 192, 1)',
        borderWidth: 1
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      scales: {
        x: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'Number of articles'
          }
        }
      },
      plugins: {
        title: {
          display: true,
          text: 'Most prolific authors'
        }
      }
    }
  });
}

// Article search function
function searchArticles() {
  const input = document.getElementById('searchInput');
  const filter = input.value.toUpperCase();
  
  // If input is empty, clear results and apply only filters
  if (filter.length < 3) {
    document.getElementById('searchResults').innerHTML = "";
    applyFilters();
    return;
  }
  
  // Apply search and filters
  applyFilters(filter);
}

// Apply filters
function applyFilters(searchTerm = null) {
  const yearFilter = document.getElementById('yearFilter').value;
  const categoryFilter = document.getElementById('categoryFilter').value;
  const searchFilter = searchTerm || document.getElementById('searchInput').value.toUpperCase();
  
  // Filter articles
  let filteredArticles = [...articlesData];
  
  // Apply year filter
  if (yearFilter) {
    filteredArticles = filteredArticles.filter(article => 
      article.published_date && article.published_date.startsWith(yearFilter)
    );
  }
  
  // Apply category filter
  if (categoryFilter) {
    filteredArticles = filteredArticles.filter(article => 
      article.categories && article.categories.includes(categoryFilter)
    );
  }
  
  // Apply search filter
  if (searchFilter && searchFilter.length >= 3) {
    filteredArticles = filteredArticles.filter(article => {
      const searchText = (article.title + " " + article.authors + " " + article.categories).toUpperCase();
      return searchText.includes(searchFilter);
    });
  }
  
  // Display results
  displaySearchResults(filteredArticles, searchFilter, yearFilter, categoryFilter);
}

// Display search results
function displaySearchResults(results, searchTerm, yearFilter, categoryFilter) {
  const resultsDiv = document.getElementById('searchResults');
  
  // Create a summary of applied filters
  let filterSummary = '';
  if (searchTerm && searchTerm.length >= 3) {
    filterSummary += `with term "${searchTerm}" `;
  }
  if (yearFilter) {
    filterSummary += `from year ${yearFilter} `;
  }
  if (categoryFilter) {
    filterSummary += `in category ${categoryFilter} `;
  }
  
  if (results.length > 0) {
    const limit = 50;  // Limit the number of displayed results
    const isLimited = results.length > limit;
    
    let tableHTML = `<h3>Results ${filterSummary}(${results.length}${isLimited ? `, showing first ${limit}` : ''})</h3>
      <table>
        <tr>
          <th>Date</th>
          <th>Authors</th>
          <th>Title</th>
          <th>Categories</th>
          <th>Link</th>
        </tr>`;
    
    // Limit displayed results
    const displayResults = results.slice(0, limit);
    
    for (let i = 0; i < displayResults.length; i++) {
      const article = displayResults[i];
      tableHTML += `<tr>
        <td>${article.published_date}</td>
        <td>${article.authors}</td>
        <td>${article.title}</td>
        <td>${article.categories}</td>
        <td><a href="${article.url}" target="_blank">arXiv:${article.id}</a></td>
      </tr>`;
    }
    tableHTML += '</table>';
    
    if (isLimited) {
      tableHTML += `<p class="results-note">Refine your search to see more results.</p>`;
    }
    
    resultsDiv.innerHTML = tableHTML;
  } else {
    if (searchTerm || yearFilter || categoryFilter) {
      resultsDiv.innerHTML = `<p>No results found ${filterSummary}</p>`;
    } else {
      resultsDiv.innerHTML = '';
    }
  }
}

// Load data when page loads
document.addEventListener('DOMContentLoaded', loadData);
</script>

<style>
/* Main container */
body {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  line-height: 1.6;
  color: #333;
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

/* Header */
h1 {
  color: #2c3e50;
  border-bottom: 2px solid #3498db;
  padding-bottom: 10px;
}

h2 {
  color: #2c3e50;
  margin-top: 30px;
  border-left: 4px solid #3498db;
  padding-left: 10px;
}

/* Statistics */
.stats-container {
  display: flex;
  justify-content: space-between;
  margin: 30px 0;
  flex-wrap: wrap;
}

.stat-box {
  background-color: #f8f9fa;
  border-radius: 8px;
  padding: 20px;
  text-align: center;
  flex: 1;
  margin: 0 10px;
  box-shadow: 0 2px 5px rgba(0,0,0,0.1);
  min-width: 200px;
  margin-bottom: 15px;
}

.stat-number {
  display: block;
  font-size: 2.5rem;
  font-weight: bold;
  color: #3498db;
}

.stat-label {
  font-size: 1rem;
  color: #7f8c8d;
}

/* Search container */
.search-container {
  margin: 20px 0;
}

#searchInput {
  width: 100%;
  padding: 12px 15px;
  margin-bottom: 15px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 16px;
  box-shadow: inset 0 1px 3px rgba(0,0,0,0.1);
}

.filter-container {
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
}

.filter-container select {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background-color: white;
  font-size: 14px;
}

/* Tables */
table {
  width: 100%;
  border-collapse: collapse;
  margin: 20px 0;
  background-color: white;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

th, td {
  padding: 12px 15px;
  text-align: left;
  border-bottom: 1px solid #ddd;
}

th {
  background-color: #f8f9fa;
  font-weight: bold;
  color: #2c3e50;
}

tr:hover {
  background-color: #f5f5f5;
}

/* Chart containers */
.chart-container {
  margin: 30px 0;
  background-color: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 5px rgba(0,0,0,0.1);
  height: 400px;
}

/* Download buttons */
.download-buttons {
  display: flex;
  gap: 15px;
  margin: 30px 0;
  flex-wrap: wrap;
}

.download-button {
  display: inline-block;
  background-color: #3498db;
  color: white;
  padding: 12px 20px;
  text-decoration: none;
  border-radius: 4px;
  font-weight: bold;
  transition: background-color 0.3s ease;
}

.download-button:hover {
  background-color: #2980b9;
}

/* Loading and error messages */
.loading-message, .error-message {
  text-align: center;
  padding: 20px;
  color: #7f8c8d;
}

#loadingIndicator {
  text-align: center;
  padding: 20px;
  background-color: #f8f9fa;
  border-radius: 4px;
  margin: 20px 0;
}

.error-message {
  color: #e74c3c;
  background-color: #fadbd8;
  padding: 10px;
  border-radius: 4px;
}

.results-note {
  font-style: italic;
  color: #7f8c8d;
  margin-top: 10px;
}

/* Responsive */
@media (max-width: 768px) {
  .stats-container {
    flex-direction: column;
  }
  
  .stat-box {
    margin: 0 0 15px 0;
  }
  
  .filter-container {
    flex-direction: column;
  }
  
  .chart-container {
    height: 300px;
  }
  
  table {
    display: block;
    overflow-x: auto;
  }
}
</style>
"""
    
    # Write content to index.md file
    with open("index.md", "w", encoding="utf-8") as f:
        f.write(index_content)
    
    print(f"The index.md file has been successfully generated (updated: {current_date}).")

def main():
    """Main function to generate the index.md file"""
    try:
        generate_index_md()
    except Exception as e:
        print(f"Error generating index.md file: {e}")

if __name__ == "__main__":
    main()
