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
const detailModal = new bootstrap.Modal(document.getElementById('detailModal'));
const dataSourceStatus = document.getElementById('dataSourceStatus');

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
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
                currentSortOrder = (currentSortOrder === 'asc') ? 'desc' : 'asc';
            } else {
                // Farklı butona basıldıysa varsayılan yönü kullan
                currentSortBy = sortBy;
                currentSortOrder = sortOrder;
            }

            // Aktif butonu güncelle
            sortButtons.forEach(b => b.classList.remove('active'));
            this.classList.add('active');

            performSearch();
        });
    });

    // Autocomplete
    createAutocomplete();
});

function createAutocomplete() {
    autocompleteList = document.createElement('div');
    autocompleteList.setAttribute('id', 'autocomplete-list');
    autocompleteList.setAttribute('class', 'autocomplete-items list-group position-absolute w-100');
    autocompleteList.style.zIndex = 1000;
    searchInput.closest('.input-group').appendChild(autocompleteList);

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
                    showUniversityDetail(uni['Program Kodu']);
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
        <div class="university-card" onclick="showUniversityDetail('${uni['Program Kodu']}')">
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
                    <div class="col-md-6">
                        <i class="fas fa-chart-line me-1"></i>
                        <strong>2024 Puanı:</strong> ${uni['2024 YKS En Küçük Puanı']}
                    </div>
                    <div class="col-md-6">
                        <i class="fas fa-trophy me-1"></i>
                        <strong>Başarı Sırası:</strong> ${uni['2024 Başarı Sırası']}
                    </div>
                </div>
            </div>
        </div>
    `).join('');
    
    resultsContainer.innerHTML = html;
}

// Show university details in modal
async function showUniversityDetail(programKodu) {
    try {
        const response = await fetch(`/api/universite/${programKodu}`);
        const university = await response.json();
        
        if (response.ok) {
            document.getElementById('modalTitle').innerHTML = `
                <i class="fas fa-university me-2"></i>${university['Üniversite Adı']}
            `;
            
            // Detaylar butonunu güncelle
            document.getElementById('detaylarBtn').href = `/detay/${university['Program Kodu']}`;
            
            document.getElementById('modalBody').innerHTML = `
                <div class="row">
                    <div class="col-md-6">
                        <div class="detail-item">
                            <span class="detail-label">Program Kodu:</span>
                            <span class="detail-value">${university['Program Kodu']}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Fakülte Adı:</span>
                            <span class="detail-value">${university['Fakülte Adı']}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Ülke:</span>
                            <span class="detail-value">${university['Ülke'] || 'Türkiye'}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Şehir:</span>
                            <span class="detail-value">${university['Şehir']}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Grup:</span>
                            <span class="detail-value">${university['Grup']}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Program Adı:</span>
                            <span class="detail-value">${university['Program Adı']}</span>
                        </div>
                        ${university['Tür'] ? `
                        <div class="detail-item">
                            <span class="detail-label">Tür:</span>
                            <span class="detail-value">${university['Tür']}</span>
                        </div>
                        ` : ''}
                    </div>
                    <div class="col-md-6">
                        <div class="detail-item">
                            <span class="detail-label">Kontenjan:</span>
                            <span class="detail-value">${university['Kontenjan']}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">2024 Başarı Sırası:</span>
                            <span class="detail-value">${university['2024 Başarı Sırası']}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">2024 YKS En Küçük Puanı:</span>
                            <span class="detail-value">${university['2024 YKS En Küçük Puanı']}</span>
                        </div>
                    </div>
                </div>

            `;
            
            detailModal.show();
        } else {
            showError('Üniversite detayları yüklenirken bir hata oluştu.');
        }
    } catch (error) {
        console.error('Error loading university details:', error);
        showError('Üniversite detayları yüklenirken bir hata oluştu.');
    }
}

// Perform search with current filters
function performSearch() {
    currentSearch = searchInput.value.trim();
    currentUlke = ulkeFilter.value;
    currentSehir = sehirFilter.value;
    currentGrup = grupFilter.value;
    currentTur = turFilter.value;
    
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
    
    // Tüm filtreleri sıfırla
    loadFilters();
    
    loadUniversities();
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