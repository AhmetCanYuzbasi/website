// Global variables
let currentSortBy = 'Üniversite Adı';
let currentSortOrder = 'asc';
let currentSearch = '';
let currentUlke = '';
let currentSehir = '';
let currentGrup = '';
let currentTur = '';
let autocompleteList;

// DOM elements
const searchInput = document.getElementById('searchInput');
const searchBtn = document.getElementById('searchBtn');
const ulkeFilter = document.getElementById('ulkeFilter');
const sehirFilter = document.getElementById('sehirFilter');
const grupFilter = document.getElementById('grupFilter');
const turFilter = document.getElementById('turFilter');
const clearFiltersBtn = document.getElementById('clearFilters');
const resultsContainer = document.getElementById('resultsContainer');
const sortButtons = document.querySelectorAll('.sort-btn');
const dataSourceStatus = document.getElementById('dataSourceStatus');

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    // URL'den filtreleri geri yükle
    restoreFiltersFromURL();
    
    checkDataSourceStatus();
    loadFilters();
    loadUniversities();
    
    // Search functionality
    searchBtn.addEventListener('click', performSearch);
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            performSearch();
        }
    });
    
    // Filter functionality - tüm filtreler birbirine bağlı
    ulkeFilter.addEventListener('change', function() {
        updateAllFilters('ulke');
        performSearch();
    });
    sehirFilter.addEventListener('change', function() {
        updateAllFilters('sehir');
        performSearch();
    });
    grupFilter.addEventListener('change', function() {
        updateAllFilters('grup');
        performSearch();
    });
    turFilter.addEventListener('change', function() {
        updateAllFilters('tur');
        performSearch();
    });
    clearFiltersBtn.addEventListener('click', clearFilters);
    
    // Sort functionality
    sortButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const sortBy = this.dataset.sort;
            let sortOrder = this.dataset.order;

            if (currentSortBy === sortBy) {
                // Aynı butona tekrar basıldıysa yönü ters çevir
                currentSortBy = sortBy;
                currentSortOrder = (currentSortBy === sortBy && currentSortOrder === 'asc') ? 'desc' : 'asc';
            } else {
                // Farklı butona basıldıysa varsayılan yönü kullan
                currentSortBy = sortBy;
                currentSortOrder = sortOrder;
            }

            // Aktif butonu güncelle
            sortButtons.forEach(b => b.classList.remove('active'));
            this.classList.add('active');

            // URL'yi güncelle
            updateURL();

            performSearch();
        });
    });

    // Autocomplete
    createAutocomplete();
});

// URL'den filtreleri geri yükle
function restoreFiltersFromURL() {
    const urlParams = new URLSearchParams(window.location.search);
    
    if (urlParams.has('search')) {
        currentSearch = urlParams.get('search');
        searchInput.value = currentSearch;
    }
    
    if (urlParams.has('ulke')) {
        currentUlke = urlParams.get('ulke');
    }
    
    if (urlParams.has('sehir')) {
        currentSehir = urlParams.get('sehir');
    }
    
    if (urlParams.has('grup')) {
        currentGrup = urlParams.get('grup');
    }
    
    if (urlParams.has('tur')) {
        currentTur = urlParams.get('tur');
    }
    
    if (urlParams.has('sort_by')) {
        currentSortBy = urlParams.get('sort_by');
    }
    
    if (urlParams.has('sort_order')) {
        currentSortOrder = urlParams.get('sort_order');
    }
    
    // Sıralama butonlarını güncelle
    updateSortButtons();
}

// URL'yi güncelle
function updateURL() {
    const urlParams = new URLSearchParams();
    
    if (currentSearch) urlParams.set('search', currentSearch);
    if (currentUlke) urlParams.set('ulke', currentUlke);
    if (currentSehir) urlParams.set('sehir', currentSehir);
    if (currentGrup) urlParams.set('grup', currentGrup);
    if (currentTur) urlParams.set('tur', currentTur);
    if (currentSortBy) urlParams.set('sort_by', currentSortBy);
    if (currentSortOrder) urlParams.set('sort_order', currentSortOrder);
    
    const newURL = window.location.pathname + (urlParams.toString() ? '?' + urlParams.toString() : '');
    window.history.replaceState({}, '', newURL);
}

// Sıralama butonlarını güncelle
function updateSortButtons() {
    sortButtons.forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.sort === currentSortBy) {
            btn.classList.add('active');
        }
    });
}

function createAutocomplete() {
    autocompleteList = document.createElement('div');
    autocompleteList.setAttribute('id', 'autocomplete-list');
    autocompleteList.setAttribute('class', 'autocomplete-items list-group position-absolute w-100');
    autocompleteList.style.zIndex = 1000;
    searchInput.closest('.search-section').appendChild(autocompleteList);

    searchInput.addEventListener('input', async function() {
        const val = this.value.trim();
        if (!val) {
            autocompleteList.innerHTML = '';
            autocompleteList.style.display = 'none';
            return;
        }
        // Fetch suggestions
        try {
            const params = new URLSearchParams({ search: val, sort_by: 'Üniversite Adı', sort_order: 'asc' });
            const response = await fetch(`/api/universiteler?${params}`);
            const universities = await response.json();
            autocompleteList.innerHTML = '';
            universities.slice(0, 10).forEach(uni => {
                const item = document.createElement('button');
                item.type = 'button';
                item.className = 'list-group-item list-group-item-action';
                item.textContent = `${uni['Üniversite Adı']} - ${uni['Program Adı']}`;
                item.onclick = function(e) {
                    e.preventDefault();
                    searchInput.value = uni['Üniversite Adı'];
                    autocompleteList.innerHTML = '';
                    autocompleteList.style.display = 'none';
                    // Direkt detay sayfasına git
                    window.location.href = `/detay/${uni['Program Kodu']}`;
                };
                autocompleteList.appendChild(item);
            });
            autocompleteList.style.display = universities.length ? 'block' : 'none';
        } catch (error) {
            autocompleteList.innerHTML = '';
            autocompleteList.style.display = 'none';
        }
    });

    // Kapatma
    document.addEventListener('click', function(e) {
        if (e.target !== searchInput) {
            autocompleteList.innerHTML = '';
            autocompleteList.style.display = 'none';
        }
    });
}

// Check data source status
async function checkDataSourceStatus() {
    try {
        const response = await fetch('/api/status');
        const status = await response.json();
        
        if (status.sheets_connected && status.sheet_configured) {
            dataSourceStatus.innerHTML = `
                <span class="badge bg-success">
                    <i class="fas fa-cloud me-1"></i>
                    Google Sheets Bağlı (${status.data_count} kayıt)
                </span>
            `;
        } else if (status.data_source === 'Excel File') {
            dataSourceStatus.innerHTML = `
                <span class="badge bg-warning">
                    <i class="fas fa-file-excel me-1"></i>
                    Excel Dosyası (${status.data_count} kayıt)
                </span>
            `;
        } else {
            dataSourceStatus.innerHTML = `
                <span class="badge bg-danger">
                    <i class="fas fa-exclamation-triangle me-1"></i>
                    Veri Kaynağı Hatası
                </span>
            `;
        }
    } catch (error) {
        console.error('Status check error:', error);
        dataSourceStatus.innerHTML = `
            <span class="badge bg-danger">
                <i class="fas fa-exclamation-triangle me-1"></i>
                Bağlantı Hatası
            </span>
        `;
    }
}

// Load filter options
async function loadFilters() {
    try {
        const response = await fetch('/api/filtreler');
        const data = await response.json();
        
        // Populate country filter
        data.ulkeler.forEach(ulke => {
            const option = document.createElement('option');
            option.value = ulke;
            option.textContent = ulke;
            ulkeFilter.appendChild(option);
        });
        
        // Initially populate city filter with all cities
        data.sehirler.forEach(sehir => {
            const option = document.createElement('option');
            option.value = sehir;
            option.textContent = sehir;
            sehirFilter.appendChild(option);
        });
        
        // Populate group filter
        data.gruplar.forEach(grup => {
            const option = document.createElement('option');
            option.value = grup;
            option.textContent = grup;
            grupFilter.appendChild(option);
        });
        
        // Populate type filter
        if (data.turler && data.turler.length > 0) {
            data.turler.forEach(tur => {
                const option = document.createElement('option');
                option.value = tur;
                option.textContent = tur;
                turFilter.appendChild(option);
            });
        }
        
        // URL'den geri yüklenen değerleri seç
        if (currentUlke) ulkeFilter.value = currentUlke;
        if (currentSehir) sehirFilter.value = currentSehir;
        if (currentGrup) grupFilter.value = currentGrup;
        if (currentTur) turFilter.value = currentTur;
        
    } catch (error) {
        console.error('Error loading filters:', error);
    }
}

// Update city filter based on selected country (legacy function)
async function updateCityFilter() {
    await updateAllFilters('ulke');
}

// Update all filters based on current selections
async function updateAllFilters(changedFilter) {
    try {
        // Mevcut seçimleri sakla
        const currentValues = {
            ulke: ulkeFilter.value,
            sehir: sehirFilter.value,
            grup: grupFilter.value,
            tur: turFilter.value
        };
        
        // API'den dinamik filtreleri al
        const params = new URLSearchParams();
        if (currentValues.ulke) params.append('ulke', currentValues.ulke);
        if (currentValues.sehir) params.append('sehir', currentValues.sehir);
        if (currentValues.grup) params.append('grup', currentValues.grup);
        if (currentValues.tur) params.append('tur', currentValues.tur);
        
        const response = await fetch(`/api/dinamik-filtreler?${params}`);
        const data = await response.json();
        
        // Ülke filtresi (her zaman tam liste)
        updateFilterOptions(ulkeFilter, data.ulkeler, currentValues.ulke);
        
        // Diğer filtreler - değişen filtreye göre güncelle
        if (changedFilter !== 'sehir') {
            updateFilterOptions(sehirFilter, data.sehirler, currentValues.sehir);
        }
        if (changedFilter !== 'grup') {
            updateFilterOptions(grupFilter, data.gruplar, currentValues.grup);
        }
        if (changedFilter !== 'tur') {
            updateFilterOptions(turFilter, data.turler, currentValues.tur);
        }
        
    } catch (error) {
        console.error('Error updating filters:', error);
    }
}

// Helper function to update filter options
function updateFilterOptions(filterElement, options, currentValue) {
    // Mevcut seçimi sakla
    const previousValue = currentValue;
    
    // Filtreyi temizle
    filterElement.innerHTML = '<option value="">Tümü</option>';
    
    // Yeni seçenekleri ekle
    options.forEach(option => {
        const optionElement = document.createElement('option');
        optionElement.value = option;
        optionElement.textContent = option;
        filterElement.appendChild(optionElement);
    });
    
    // Eğer önceki seçim hala mevcut listede varsa, onu koru
    if (previousValue && options.includes(previousValue)) {
        filterElement.value = previousValue;
    } else {
        // Önceki seçim artık geçerli değilse "Tümü" yap
        filterElement.value = '';
    }
}

// Load universities with current filters
async function loadUniversities() {
    showLoading();
    
    try {
        const params = new URLSearchParams({
            search: currentSearch,
            ulke: currentUlke,
            sehir: currentSehir,
            grup: currentGrup,
            tur: currentTur,
            sort_by: currentSortBy,
            sort_order: currentSortOrder
        });
        
        const response = await fetch(`/api/universiteler?${params}`);
        const universities = await response.json();
        console.log('Gelen üniversite sayısı:', universities.length, universities);
        displayUniversities(universities);
        updateStats(universities);
    } catch (error) {
        console.error('Error loading universities:', error);
        showError('Üniversiteler yüklenirken bir hata oluştu.');
    }
}

// Display universities in the results container
function displayUniversities(universities) {
    if (universities.length === 0) {
        resultsContainer.innerHTML = `
            <div class="text-center py-5">
                <i class="fas fa-search fa-3x text-muted mb-3"></i>
                <h4 class="text-muted">Sonuç bulunamadı</h4>
                <p class="text-muted">Arama kriterlerinizi değiştirmeyi deneyin.</p>
            </div>
        `;
        return;
    }
    
    const html = universities.map(uni => `
        <div class="university-card" onclick="goToUniversityDetail('${uni['Program Kodu']}')">
            <div class="university-name">
                <i class="fas fa-university me-2 text-primary"></i>
                ${uni['Üniversite Adı']}
            </div>
            <div class="university-info">
                <div class="row">
                    <div class="col-md-3">
                        <i class="fas fa-globe me-1"></i>
                        <strong>Ülke:</strong> ${uni['Ülke'] || 'Türkiye'}
                    </div>
                    <div class="col-md-3">
                        <i class="fas fa-map-marker-alt me-1"></i>
                        <strong>Şehir:</strong> ${uni['Şehir']}
                    </div>
                    <div class="col-md-3">
                        <i class="fas fa-graduation-cap me-1"></i>
                        <strong>Fakülte:</strong> ${uni['Fakülte Adı']}
                    </div>
                    <div class="col-md-3">
                        <i class="fas fa-users me-1"></i>
                        <strong>Kontenjan:</strong> ${uni['Kontenjan']}
                    </div>
                </div>
                <div class="row mt-2">
                    <div class="col-md-4">
                        <i class="fas fa-book me-1"></i>
                        <strong>Program:</strong> ${uni['Program Adı']}
                    </div>
                    <div class="col-md-4">
                        <i class="fas fa-chart-line me-1"></i>
                        <strong>2024 Puanı:</strong> ${uni['2024 YKS En Küçük Puanı']}
                    </div>
                    ${uni['Tür'] ? `
                    <div class="col-md-4">
                        <i class="fas fa-tag me-1"></i>
                        <strong>Tür:</strong> ${uni['Tür']}
                    </div>
                    ` : ''}
                </div>
                <div class="row mt-2">
                    <div class="col-md-4">
                        <i class="fas fa-chart-line me-1"></i>
                        <strong>2024 Puanı:</strong> ${uni['2024 YKS En Küçük Puanı']}
                    </div>
                    <div class="col-md-4">
                        <i class="fas fa-trophy me-1"></i>
                        <strong>Başarı Sırası:</strong> ${uni['2024 Başarı Sırası']}
                    </div>
                    <div class="col-md-4">
                        <i class="fas fa-chart-bar me-1"></i>
                        <strong>Başarı Sırası Aralığı:</strong> ${uni['2024 Başarı Sırası Aralığı'] || '-'}
                    </div>
                </div>
                ${uni['Wikipedia Alan Adı'] ? `
                <div class="row mt-2">
                    <div class="col-12">
                        <a href="${uni['Wikipedia Alan Adı']}" target="_blank" class="wikipedia-link-card" onclick="event.stopPropagation();">
                            <i class="fab fa-wikipedia-w me-2"></i>Wikipedia'da Görüntüle
                        </a>
                    </div>
                </div>
                ` : ''}
            </div>
        </div>
    `).join('');
    
    resultsContainer.innerHTML = html;
}

// Direkt detay sayfasına git
function goToUniversityDetail(programKodu) {
    // Mevcut filtreleri URL'ye ekle
    const urlParams = new URLSearchParams();
    
    if (currentSearch) urlParams.set('search', currentSearch);
    if (currentUlke) urlParams.set('ulke', currentUlke);
    if (currentSehir) urlParams.set('sehir', currentSehir);
    if (currentGrup) urlParams.set('grup', currentGrup);
    if (currentTur) urlParams.set('tur', currentTur);
    if (currentSortBy) urlParams.set('sort_by', currentSortBy);
    if (currentSortOrder) urlParams.set('sort_order', currentSortOrder);
    
    const returnURL = window.location.pathname + (urlParams.toString() ? '?' + urlParams.toString() : '');
    
    // Detay sayfasına git ve geri dönüş URL'sini ekle
    window.location.href = `/detay/${programKodu}?return=${encodeURIComponent(returnURL)}`;
}

// Perform search with current filters
function performSearch() {
    currentSearch = searchInput.value.trim();
    currentUlke = ulkeFilter.value;
    currentSehir = sehirFilter.value;
    currentGrup = grupFilter.value;
    currentTur = turFilter.value;
    
    // URL'yi güncelle
    updateURL();
    
    loadUniversities();
}

// Clear all filters
function clearFilters() {
    searchInput.value = '';
    ulkeFilter.value = '';
    sehirFilter.value = '';
    grupFilter.value = '';
    turFilter.value = '';
    
    currentSearch = '';
    currentUlke = '';
    currentSehir = '';
    currentGrup = '';
    currentTur = '';
    
    // Reset sort buttons
    sortButtons.forEach(btn => btn.classList.remove('active'));
    sortButtons[0].classList.add('active'); // First button (Üniversite Adı)
    
    currentSortBy = 'Üniversite Adı';
    currentSortOrder = 'asc';
    
    // URL'yi temizle
    updateURL();
    
    // Tüm filtreleri sıfırla
    loadFilters();
    
    loadUniversities();
}

// Update statistics
function updateStats(universities) {
    const uniqueUlkeler = [...new Set(universities.map(u => u['Ülke']).filter(Boolean))];
    const uniqueSehirler = [...new Set(universities.map(u => u['Şehir']).filter(Boolean))];
    
    document.getElementById('totalCount').textContent = universities.length;
    document.getElementById('ulkeCount').textContent = uniqueUlkeler.length;
    document.getElementById('sehirCount').textContent = uniqueSehirler.length;
    document.getElementById('filteredCount').textContent = universities.length;
}

// Show loading state
function showLoading() {
    resultsContainer.innerHTML = `
        <div class="loading">
            <i class="fas fa-spinner fa-spin fa-2x mb-3"></i>
            <p>Üniversiteler yükleniyor...</p>
        </div>
    `;
}

// Show error message
function showError(message) {
    resultsContainer.innerHTML = `
        <div class="text-center py-5">
            <i class="fas fa-exclamation-triangle fa-3x text-danger mb-3"></i>
            <h4 class="text-danger">Hata</h4>
            <p class="text-muted">${message}</p>
        </div>
    `;
} 