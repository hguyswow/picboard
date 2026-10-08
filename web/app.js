// web/app.js - 사진대지 웹 스튜디오 (다중선택 & 스탬프 설정 영구저장 탑재)
let items = [];
let currentIndex = -1;
let lastCheckedIndex = -1; // Shift 다중 선택용
let blankPagesCount = 0;
let presets = { work_types: [], locations: [], contents: [], combos: [] };

const DEFAULT_STAMP_CONFIG = {
  enabled: true,
  position: "bottom_right",
  show_project: false,
  show_work_type: true,
  show_location: true,
  show_content: true,
  show_date: true,
  custom_text: "",
  font_size: 18,
  text_color: "#ffffff",
  bg_color: "#000000",
  bg_alpha: 0.65,
  border: true,
  hide_labels: false
};

let stampConfig = Object.assign({}, DEFAULT_STAMP_CONFIG);

const DEFAULT_TABLE_CONFIG = {
  row_count: 2,
  fields: [
    { id: "f1", key: "work_type", label: "공    종", enabled: true },
    { id: "f2", key: "content", label: "내       용", enabled: true },
    { id: "f3", key: "location", label: "위    치", enabled: true },
    { id: "f4", key: "date_str", label: "촬 영 일 자", enabled: true }
  ]
};

let tableConfig = JSON.parse(JSON.stringify(DEFAULT_TABLE_CONFIG));

document.addEventListener("DOMContentLoaded", () => {
  loadStampConfig();
  loadTableConfig();
  initEventListeners();
  initUiMode();
  loadPresets();
  updateView();
  restoreFromStorageIfAny();
});

function initEventListeners() {
  // 1. 파일 및 폴더 추가
  document.getElementById("fileInput").addEventListener("change", handleFileSelect);
  document.getElementById("folderInput").addEventListener("change", handleFolderSelect);

  // 2. 클립보드 붙여넣기 (Ctrl+V)
  window.addEventListener("paste", handleClipboardPaste);
  document.getElementById("btnPaste").addEventListener("click", () => {
    alert("클립보드에 복사된 이미지가 있다면 어디서나 Ctrl+V를 누르시면 즉시 추가됩니다!");
  });

  // 3. 드래그 앤 드롭
  const dropZone = document.getElementById("photoList");
  dropZone.addEventListener("dragover", (e) => { e.preventDefault(); dropZone.style.background = "#eef5ff"; });
  dropZone.addEventListener("dragleave", () => { dropZone.style.background = ""; });
  dropZone.addEventListener("drop", handleDrop);

  // 4. 공사명 변경
  document.getElementById("projectName").addEventListener("input", (e) => {
    renderPreview();
    autoSaveToStorage();
  });

  // 5. 정렬, 전체선택 및 스탬프/삭제 액션
  document.getElementById("sortSelect").addEventListener("change", handleSort);
  document.getElementById("selectAllCheckbox").addEventListener("change", handleSelectAll);
  document.getElementById("btnToggleAllStamps").addEventListener("click", toggleAllStamps);
  document.getElementById("btnDeleteSelected").addEventListener("click", deleteSelectedItems);

  // 6. 편집 폼 입력 이벤트
  document.getElementById("fieldWork").addEventListener("input", handleFieldEdit);
  document.getElementById("fieldLoc").addEventListener("input", handleFieldEdit);
  const fieldStamp = document.getElementById("fieldStampContent");
  if (fieldStamp) fieldStamp.addEventListener("input", handleFieldEdit);
  document.getElementById("fieldContent").addEventListener("input", handleFieldEdit);
  document.getElementById("fieldDate").addEventListener("input", handleFieldEdit);
  const fieldC1 = document.getElementById("fieldCustom1");
  if (fieldC1) fieldC1.addEventListener("input", handleFieldEdit);
  const fieldC2 = document.getElementById("fieldCustom2");
  if (fieldC2) fieldC2.addEventListener("input", handleFieldEdit);
  document.getElementById("cropModeSelect").addEventListener("change", handleCropChange);
  document.getElementById("itemStampToggle").addEventListener("change", handleStampToggle);

  // 7. 회전 및 여백 컨트롤
  document.getElementById("btnRotateCw").addEventListener("click", () => rotateCurrentImage(90));
  document.getElementById("btnRotateCcw").addEventListener("click", () => rotateCurrentImage(-90));
  document.getElementById("sliderPadding").addEventListener("input", handlePaddingChange);

  // 8. 개별 사진 날짜 퀵 추출 버튼
  document.getElementById("btnExtractExif").addEventListener("click", extractSingleExif);
  document.getElementById("btnExtractMtime").addEventListener("click", extractSingleMtime);

  // 9. 날짜 추출 전용 모달 열기 & 적용
  document.getElementById("btnOpenDateModal").addEventListener("click", openDateModal);
  document.getElementById("btnBatchDateQuick").addEventListener("click", openDateModal);
  document.getElementById("btnApplyDateExtraction").addEventListener("click", applyDateExtraction);

  // 10. 일괄 적용 및 확장 모달
  document.getElementById("btnApplyBatch").addEventListener("click", applyBatch);
  const btnOpenBatchModal = document.getElementById("btnOpenBatchModal");
  if (btnOpenBatchModal) btnOpenBatchModal.addEventListener("click", openBatchModal);
  const btnApplyModalBatch = document.getElementById("btnApplyModalBatch");
  if (btnApplyModalBatch) btnApplyModalBatch.addEventListener("click", applyModalBatch);
  const btnModalBatchExif = document.getElementById("btnModalBatchExif");
  if (btnModalBatchExif) btnModalBatchExif.addEventListener("click", extractModalBatchExif);
  const btnModalBatchMtime = document.getElementById("btnModalBatchMtime");
  if (btnModalBatchMtime) btnModalBatchMtime.addEventListener("click", extractModalBatchMtime);
  const btnModalBatchToday = document.getElementById("btnModalBatchToday");
  if (btnModalBatchToday) btnModalBatchToday.addEventListener("click", () => {
    const today = formatDateFromIso(new Date().toISOString(), "YYYY.MM.DD");
    document.getElementById("modalBatchDate").value = today;
  });

  // 11. 빈 페이지 추가 및 삭제 버튼
  document.getElementById("btnAddBlankPage").addEventListener("click", () => {
    blankPagesCount++;
    renderPreview();
    autoSaveToStorage();
    const wrapper = document.getElementById("a4PagesContainer");
    wrapper.scrollTop = wrapper.scrollHeight;
    const total = document.querySelectorAll('.a4-page-sheet').length;
    showToastNotification(`빈 사진대지 1페이지가 추가되었습니다. (총 ${total}페이지)`);
  });

  const btnRemove = document.getElementById("btnRemoveBlankPage");
  if (btnRemove) {
    btnRemove.addEventListener("click", removeBlankPage);
  }

  // 12. 프로젝트 저장 / 불러오기 / ZIP 다운로드
  document.getElementById("btnSaveProject").addEventListener("click", exportProjectFile);
  document.getElementById("projectFileInput").addEventListener("change", importProjectFile);
  document.getElementById("btnExportZip").addEventListener("click", exportImagesZip);

  // 13. 내보내기 & 인쇄
  document.getElementById("btnExportPdf").addEventListener("click", exportPdf);
  document.getElementById("btnExportExcel").addEventListener("click", exportExcel);
  document.getElementById("btnPrint").addEventListener("click", () => window.print());
  const btnShutdown = document.getElementById("btnShutdown");
  if (btnShutdown) btnShutdown.addEventListener("click", handleShutdown);

  // 14. 모달 이벤트 (스탬프 설정 & 프리셋 & 표 설정)
  document.getElementById("btnOpenStampSettings").addEventListener("click", openStampModal);
  document.getElementById("btnSaveStampSettings").addEventListener("click", saveStampSettings);
  document.getElementById("btnSaveStampAsDefault").addEventListener("click", saveStampAsDefault);
  document.getElementById("btnResetStampSettings").addEventListener("click", resetStampToDefault);
  document.getElementById("btnOpenPresets").addEventListener("click", () => openModal("presetModal"));
  document.getElementById("btnAddCombo").addEventListener("click", addComboPreset);
  document.getElementById("comboPresetSelect").addEventListener("change", handlePresetSelect);

  // 표 커스텀 설정 모달 이벤트
  const btnOpenTable = document.getElementById("btnOpenTableSettings");
  if (btnOpenTable) btnOpenTable.addEventListener("click", openTableModal);
  const btnSaveTableDef = document.getElementById("btnSaveTableAsDefault");
  if (btnSaveTableDef) btnSaveTableDef.addEventListener("click", saveTableConfigAsDefault);
  const btnResetTable = document.getElementById("btnResetTableConfig");
  if (btnResetTable) btnResetTable.addEventListener("click", resetTableConfigToDefault);
  const btnApplyTable = document.getElementById("btnApplyTableConfig");
  if (btnApplyTable) btnApplyTable.addEventListener("click", applyTableConfig);

  const btnPStd = document.getElementById("btnTablePresetStd");
  if (btnPStd) btnPStd.addEventListener("click", () => applyTablePreset('standard'));
  const btnPSimple = document.getElementById("btnTablePresetSimple");
  if (btnPSimple) btnPSimple.addEventListener("click", () => applyTablePreset('simple'));
  const btnPQual = document.getElementById("btnTablePresetQuality");
  if (btnPQual) btnPQual.addEventListener("click", () => applyTablePreset('quality'));
  const btnPSafe = document.getElementById("btnTablePresetSafety");
  if (btnPSafe) btnPSafe.addEventListener("click", () => applyTablePreset('safety'));

  // 15. 사진 상세 모달 이벤트
  document.getElementById("btnSavePhotoDetail").addEventListener("click", savePhotoDetail);
  document.getElementById("btnDetailExif").addEventListener("click", () => applyDetailDateSource('exif'));
  document.getElementById("btnDetailMtime").addEventListener("click", () => applyDetailDateSource('mtime'));
  document.getElementById("btnDetailCtime").addEventListener("click", () => applyDetailDateSource('ctime'));
  document.getElementById("btnDetailToday").addEventListener("click", () => applyDetailDateSource('today'));

  const detailInputs = [
    "detailFieldDate", "detailFieldWork", "detailFieldLoc", "detailFieldStampContent", "detailFieldContent",
    "detailFieldCustom1", "detailFieldCustom2",
    "detailCropMode", "detailStampToggle"
  ];
  detailInputs.forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      el.addEventListener("input", renderDetailModalPreview);
      el.addEventListener("change", renderDetailModalPreview);
    }
  });

  document.getElementById("detailSliderPadding").addEventListener("input", (e) => {
    document.getElementById("lblDetailPaddingVal").textContent = `${e.target.value}px`;
    renderDetailModalPreview();
  });

  // 스탬프 모달 입력 시 실시간 미니 프리뷰 갱신
  const stampModalInputs = [
    "stampPosition", "stTextColor", "stAlpha", "stFontSize",
    "stShowProject", "stShowWork", "stShowLoc", "stShowContent", "stShowDate", "stBorder", "stCustomText",
    "stLabelShow", "stLabelHide"
  ];
  stampModalInputs.forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      el.addEventListener("input", updateStampModalPreview);
      el.addEventListener("change", updateStampModalPreview);
    }
  });

  // 슬라이더 라벨 & 미니 프리뷰 실시간 동기화
  document.getElementById("stFontSize").addEventListener("input", (e) => {
    document.getElementById("stFontSizeVal").textContent = `${e.target.value}pt`;
    updateStampModalPreview();
  });
  document.getElementById("stAlpha").addEventListener("input", (e) => {
    document.getElementById("stAlphaVal").textContent = `${e.target.value}%`;
    updateStampModalPreview();
  });
}

// ================= 파일 업로드 & 클립보드 =================
// ================= 파일 업로드 & 클립보드 =================
async function uploadFiles(fileList, folderName = "") {
  if (!fileList || fileList.length === 0) return;
  const formData = new FormData();
  for (const f of fileList) {
    // 3번째 인자로 순수 파일명(f.name)을 명시적으로 전달하여
    // 브라우저가 webkitRelativePath(예: "점검사진/사진.jpg")를 전달하더라도 순수 파일명으로 강제 정제
    formData.append("files", f, f.name);
  }
  formData.append("folder_name", folderName);

  try {
    const res = await fetch("/api/upload", { method: "POST", body: formData });
    if (!res.ok) {
      const errText = await res.text();
      throw new Error(errText || "업로드 실패");
    }
    const newItems = await res.json();
    if (newItems.length === 0) {
      alert("추가할 수 있는 유효한 이미지 파일(.jpg, .png 등)이 없습니다.");
      return;
    }
    newItems.forEach(it => { it.selected = false; });
    items.push(...newItems);

    if (currentIndex === -1 && items.length > 0) {
      selectItem(0);
    }
    updateView();
    autoSaveToStorage();
    const folderMsg = folderName ? `'${folderName}' 폴더에서 ` : "";
    showToastNotification(`${folderMsg}사진 ${newItems.length}장이 성공적으로 추가되었습니다!`);
  } catch (err) {
    alert("사진 업로드 중 오류 발생: " + err.message);
  }
}

function handleFileSelect(e) {
  uploadFiles(e.target.files);
  e.target.value = "";
}

function handleFolderSelect(e) {
  const files = e.target.files;
  if (!files || files.length === 0) return;
  let folderName = "폴더";
  if (files[0].webkitRelativePath) {
    const parts = files[0].webkitRelativePath.split("/");
    if (parts.length > 1) {
      folderName = parts[0];
    }
  }
  uploadFiles(files, folderName);
  e.target.value = "";
}

async function handleDrop(e) {
  e.preventDefault();
  document.getElementById("photoList").style.background = "";
  const itemsList = e.dataTransfer.items;
  if (itemsList && itemsList.length > 0) {
    const collectedFiles = [];
    let detectedFolder = "";

    async function traverseEntry(entry) {
      if (entry.isFile) {
        return new Promise((resolve) => {
          entry.file((file) => {
            collectedFiles.push(file);
            resolve();
          }, () => resolve());
        });
      } else if (entry.isDirectory) {
        if (!detectedFolder) detectedFolder = entry.name;
        const dirReader = entry.createReader();
        return new Promise((resolve) => {
          const readEntries = () => {
            dirReader.readEntries(async (entries) => {
              if (entries.length === 0) {
                resolve();
              } else {
                for (const subEntry of entries) {
                  await traverseEntry(subEntry);
                }
                readEntries();
              }
            }, () => resolve());
          };
          readEntries();
        });
      }
    }

    const promises = [];
    for (let i = 0; i < itemsList.length; i++) {
      const entry = itemsList[i].webkitGetAsEntry ? itemsList[i].webkitGetAsEntry() : null;
      if (entry) {
        promises.push(traverseEntry(entry));
      }
    }

    if (promises.length > 0) {
      await Promise.all(promises);
      if (collectedFiles.length > 0) {
        uploadFiles(collectedFiles, detectedFolder);
        return;
      }
    }
  }

  if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
    uploadFiles(e.dataTransfer.files);
  }
}

function handleClipboardPaste(e) {
  const clipItems = e.clipboardData.items;
  const filesToUpload = [];
  for (let i = 0; i < clipItems.length; i++) {
    if (clipItems[i].type.indexOf("image") !== -1) {
      const blob = clipItems[i].getAsFile();
      const fname = `clip_${Date.now()}_${i+1}.png`;
      const file = new File([blob], fname, { type: blob.type });
      filesToUpload.push(file);
    }
  }
  if (filesToUpload.length > 0) {
    uploadFiles(filesToUpload, "클립보드");
  }
}

// ================= 리스트 및 뷰 갱신 =================
function updateView() {
  updateSelectionStats();
  renderPhotoList();
  renderPreview();
}

function updateSelectionStats() {
  const total = items.length;
  const selectedCount = items.filter(it => it.selected).length;

  document.getElementById("totalCount").textContent = total;
  document.getElementById("selectedCount").textContent = selectedCount;

  const selectAllCb = document.getElementById("selectAllCheckbox");
  if (selectAllCb) {
    if (total > 0 && selectedCount === total) {
      selectAllCb.checked = true;
      selectAllCb.indeterminate = false;
    } else if (selectedCount > 0) {
      selectAllCb.checked = false;
      selectAllCb.indeterminate = true;
    } else {
      selectAllCb.checked = false;
      selectAllCb.indeterminate = false;
    }
  }

  // 하단 일괄 작업 패널 및 확장 모달 안내 텍스트 동적 변경
  const descEl = document.getElementById("batchTargetDesc");
  const btnTextEl = document.getElementById("batchApplyBtnText");
  const modalDescEl = document.getElementById("modalBatchTargetDesc");
  const modalBtnTextEl = document.getElementById("modalBatchApplyBtnText");

  if (selectedCount > 0) {
    if (descEl) descEl.textContent = `선택 ${selectedCount}장 대상`;
    if (btnTextEl) btnTextEl.textContent = `선택(${selectedCount}장) 적용`;
    if (modalDescEl) modalDescEl.textContent = `선택 ${selectedCount}장 대상`;
    if (modalBtnTextEl) modalBtnTextEl.textContent = `선택(${selectedCount}장) 일괄 적용`;
  } else {
    if (descEl) descEl.textContent = "전체 대상";
    if (btnTextEl) btnTextEl.textContent = `전체(${total}장) 적용`;
    if (modalDescEl) modalDescEl.textContent = `전체 ${total}장 대상`;
    if (modalBtnTextEl) modalBtnTextEl.textContent = `전체(${total}장) 일괄 적용`;
  }

  // 상단 툴바 실시간 입력 대상 배지 갱신
  const targetBadge = document.getElementById("fieldTargetBadge");
  const targetText = document.getElementById("fieldTargetText");
  if (targetBadge && targetText) {
    if (selectedCount > 0) {
      targetBadge.style.background = "#ecfdf5";
      targetBadge.style.color = "#047857";
      targetBadge.style.borderColor = "#a7f3d0";
      targetText.textContent = `선택 ${selectedCount}장 동시 입력 중`;
    } else {
      targetBadge.style.background = "#e0f2fe";
      targetBadge.style.color = "#0369a1";
      targetBadge.style.borderColor = "#bae6fd";
      targetText.textContent = (currentIndex >= 0 && currentIndex < total) ? `${currentIndex + 1}번 사진 단독 편집` : "사진 선택 안 됨";
    }
  }
}

function handleSelectAll(e) {
  const isChecked = e.target.checked;
  items.forEach(it => { it.selected = isChecked; });
  updateSelectionStats();
  renderPhotoList();
}

function handleItemSelect(idx, e) {
  if (e) e.stopPropagation();
  if (idx < 0 || idx >= items.length) return;

  const isChecked = e.target.checked;

  if (e.shiftKey && lastCheckedIndex !== -1 && lastCheckedIndex !== idx) {
    const start = Math.min(lastCheckedIndex, idx);
    const end = Math.max(lastCheckedIndex, idx);
    for (let i = start; i <= end; i++) {
      items[i].selected = isChecked;
    }
  } else {
    items[idx].selected = isChecked;
  }
  lastCheckedIndex = idx;

  updateSelectionStats();
  renderPhotoList();
}

function renderPhotoList() {
  const listEl = document.getElementById("photoList");
  if (items.length === 0) {
    listEl.innerHTML = `
      <div class="empty-state">
        <i class="fa-regular fa-images"></i>
        <p>사진 파일을 드래그 앤 드롭하거나<br><strong>[파일 추가]</strong> 또는 <strong>Ctrl+V</strong>로 붙여넣으세요.</p>
      </div>`;
    return;
  }

  listEl.innerHTML = items.map((it, idx) => `
    <div class="photo-item-card ${idx === currentIndex ? 'active' : ''} ${it.selected ? 'checked' : ''}" 
         onclick="selectItem(${idx})" 
         ondblclick="openPhotoDetailModal(${idx})" 
         title="클릭: 선택 / 더블클릭: 상세 정보 및 날짜 수정 [${it.filename}]">
      <div class="card-checkbox-wrap" onclick="event.stopPropagation()">
        <input type="checkbox" class="card-checkbox" ${it.selected ? 'checked' : ''} 
               onchange="handleItemSelect(${idx}, event)" title="사진 선택">
      </div>
      <div class="card-idx">${idx + 1}</div>
      <img class="card-thumb" src="${it.url}" style="transform: rotate(${it.rotation || 0}deg);" alt="${it.filename}">
      <div class="card-info">
        <div class="card-title">${it.filename}</div>
        <div class="card-sub">
          <span>📁 ${it.folder_name}</span>
          <span>📅 ${it.date_str}</span>
          <span>⟳ ${it.rotation || 0}°</span>
        </div>
        ${(it.stamp_content || it.content) ? `<div class="card-content-preview" style="font-size:11px; color:#475569; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; margin-top:2px;">${it.stamp_content ? `<strong style="color:#0284c7;">[${it.stamp_content}]</strong> ` : ''}${it.content || ''}</div>` : ''}
      </div>
      <span class="stamp-toggle-pill ${it.stamp_enabled ? 'on' : ''}" onclick="toggleItemStamp(event, ${idx})">
        스탬프 ${it.stamp_enabled ? 'ON' : 'OFF'}
      </span>
    </div>
  `).join("");
}

function selectItem(idx) {
  if (idx < 0 || idx >= items.length) return;
  currentIndex = idx;
  const it = items[idx];

  document.getElementById("fieldWork").value = it.work_type || "";
  document.getElementById("fieldLoc").value = it.location || "";
  const fStamp = document.getElementById("fieldStampContent");
  if (fStamp) fStamp.value = it.stamp_content || "";
  document.getElementById("fieldContent").value = it.content || "";
  document.getElementById("fieldDate").value = it.date_str || "";
  const fC1 = document.getElementById("fieldCustom1");
  if (fC1) fC1.value = it.custom1 || "";
  const fC2 = document.getElementById("fieldCustom2");
  if (fC2) fC2.value = it.custom2 || "";
  document.getElementById("cropModeSelect").value = it.crop_mode || "cover";
  document.getElementById("itemStampToggle").checked = it.stamp_enabled;

  const rot = it.rotation || 0;
  document.getElementById("lblRotation").textContent = `${rot}°`;
  const pad = it.padding || 0;
  document.getElementById("sliderPadding").value = pad;
  document.getElementById("lblPaddingVal").textContent = `${pad}px`;

  updateView();
}

function handleFieldEdit(e) {
  const fieldId = (e && e.target) ? e.target.id : "";
  const val = (e && e.target) ? e.target.value : "";

  const selectedItems = items.filter(it => it.selected);
  const targetItems = selectedItems.length > 0 ? selectedItems : (currentIndex >= 0 ? [items[currentIndex]] : []);
  if (targetItems.length === 0) return;

  targetItems.forEach(it => {
    if (fieldId === "fieldWork") it.work_type = val;
    else if (fieldId === "fieldLoc") it.location = val;
    else if (fieldId === "fieldStampContent") it.stamp_content = val;
    else if (fieldId === "fieldContent") it.content = val;
    else if (fieldId === "fieldDate") it.date_str = val;
    else if (fieldId === "fieldCustom1") it.custom1 = val;
    else if (fieldId === "fieldCustom2") it.custom2 = val;
    else {
      it.work_type = document.getElementById("fieldWork").value;
      it.location = document.getElementById("fieldLoc").value;
      const fStamp = document.getElementById("fieldStampContent");
      if (fStamp) it.stamp_content = fStamp.value;
      it.content = document.getElementById("fieldContent").value;
      it.date_str = document.getElementById("fieldDate").value;
      const fc1 = document.getElementById("fieldCustom1");
      if (fc1) it.custom1 = fc1.value;
      const fc2 = document.getElementById("fieldCustom2");
      if (fc2) it.custom2 = fc2.value;
    }
  });

  renderPreview();
  if (fieldId === "fieldDate" || fieldId === "fieldContent" || fieldId === "fieldStampContent") {
    renderPhotoList();
  }
  autoSaveToStorage();
}

function handleCropChange(e) {
  const val = e.target.value;
  const selectedItems = items.filter(it => it.selected);
  const targetItems = selectedItems.length > 0 ? selectedItems : (currentIndex >= 0 ? [items[currentIndex]] : []);
  if (targetItems.length === 0) return;

  targetItems.forEach(it => { it.crop_mode = val; });
  renderPreview();
  autoSaveToStorage();
}

// 툴바 회전 (선택된 사진들 일괄 회전 또는 현재 사진 회전)
function rotateCurrentImage(delta) {
  const selectedItems = items.filter(it => it.selected);
  if (selectedItems.length > 0) {
    selectedItems.forEach(it => {
      it.rotation = ((it.rotation || 0) + delta + 360) % 360;
    });
    if (currentIndex >= 0 && currentIndex < items.length) {
      document.getElementById("lblRotation").textContent = `${items[currentIndex].rotation || 0}°`;
    }
    updateView();
    autoSaveToStorage();
  } else if (currentIndex >= 0 && currentIndex < items.length) {
    rotateItem(null, currentIndex, delta);
  }
}

// 특정 사진 단독 회전 (슬롯 퀵버튼 또는 툴바에서 호출)
function rotateItem(event, idx, delta) {
  if (event) event.stopPropagation();
  if (idx < 0 || idx >= items.length) return;
  const it = items[idx];
  it.rotation = ((it.rotation || 0) + delta + 360) % 360;
  if (idx === currentIndex) {
    document.getElementById("lblRotation").textContent = `${it.rotation}°`;
  }
  updateView();
  autoSaveToStorage();
}

function handlePaddingChange(e) {
  const val = parseInt(e.target.value) || 0;
  document.getElementById("lblPaddingVal").textContent = `${val}px`;

  const selectedItems = items.filter(it => it.selected);
  const targetItems = selectedItems.length > 0 ? selectedItems : (currentIndex >= 0 ? [items[currentIndex]] : []);
  if (targetItems.length === 0) return;

  targetItems.forEach(it => {
    it.padding = val;
  });

  renderPreview();
  autoSaveToStorage();
}

function handleStampToggle(e) {
  const checked = e.target.checked;
  const selectedItems = items.filter(it => it.selected);
  const targetItems = selectedItems.length > 0 ? selectedItems : (currentIndex >= 0 ? [items[currentIndex]] : []);
  if (targetItems.length === 0) return;

  targetItems.forEach(it => {
    it.stamp_enabled = checked;
  });

  renderPreview();
  renderPhotoList();
  autoSaveToStorage();
}

function toggleItemStamp(event, idx) {
  if (event) event.stopPropagation();
  if (idx < 0 || idx >= items.length) return;
  items[idx].stamp_enabled = !items[idx].stamp_enabled;
  if (idx === currentIndex) {
    document.getElementById("itemStampToggle").checked = items[idx].stamp_enabled;
  }
  renderPreview();
  renderPhotoList();
  autoSaveToStorage();
}

function toggleAllStamps() {
  const selectedItems = items.filter(it => it.selected);
  const targetItems = selectedItems.length > 0 ? selectedItems : items;
  if (targetItems.length === 0) return;

  const anyOn = targetItems.some(it => it.stamp_enabled);
  const targetState = !anyOn;
  targetItems.forEach(it => { it.stamp_enabled = targetState; });

  if (currentIndex >= 0 && currentIndex < items.length) {
    document.getElementById("itemStampToggle").checked = items[currentIndex].stamp_enabled;
  }
  const label = selectedItems.length > 0 ? "선택 스탬프" : "스탬프 전체";
  document.getElementById("btnToggleAllStamps").textContent = targetState ? `${label}OFF` : `${label}ON`;
  renderPreview();
  renderPhotoList();
  autoSaveToStorage();
}

function deleteSelectedItems() {
  const selectedItems = items.filter(it => it.selected);
  if (selectedItems.length > 0) {
    if (!confirm(`선택된 ${selectedItems.length}장의 사진을 정말 삭제하시겠습니까?`)) return;
    items = items.filter(it => !it.selected);
  } else if (currentIndex >= 0 && currentIndex < items.length) {
    if (!confirm(`현재 포커스된 [${items[currentIndex].filename}] 사진을 삭제하시겠습니까?`)) return;
    items.splice(currentIndex, 1);
  } else {
    alert("삭제할 사진을 선택하세요.");
    return;
  }

  if (items.length === 0) {
    currentIndex = -1;
  } else {
    currentIndex = Math.min(currentIndex, items.length - 1);
  }
  updateView();
  if (currentIndex >= 0) selectItem(currentIndex);
  autoSaveToStorage();
}

function handleSort(e) {
  const val = (e && e.target) ? e.target.value : document.getElementById("sortSelect").value;
  let sortLabel = "";
  if (val === "name_asc") {
    items.sort((a, b) => (a.filename || "").localeCompare(b.filename || ""));
    sortLabel = "파일명 오름차순";
  } else if (val === "name_desc") {
    items.sort((a, b) => (b.filename || "").localeCompare(a.filename || ""));
    sortLabel = "파일명 내림차순";
  } else if (val === "date_asc") {
    items.sort((a, b) => (a.date_str || "").localeCompare(b.date_str || "") || (a.filename || "").localeCompare(b.filename || ""));
    sortLabel = "촬영일자 오름차순(과거순)";
  } else if (val === "date_desc") {
    items.sort((a, b) => (b.date_str || "").localeCompare(a.date_str || "") || (a.filename || "").localeCompare(b.filename || ""));
    sortLabel = "촬영일자 내림차순(최신순)";
  } else if (val === "folder") {
    items.sort((a, b) => (a.folder_name || "").localeCompare(b.folder_name || "") || (a.filename || "").localeCompare(b.filename || ""));
    sortLabel = "폴더별 묶음";
  }

  if (items.length > 0) {
    if (currentIndex >= 0 && currentIndex < items.length) {
      selectItem(currentIndex);
    } else {
      selectItem(0);
    }
  } else {
    updateView();
  }
  autoSaveToStorage();
  if (sortLabel && items.length > 1) {
    showToastNotification(`${sortLabel}으로 사진 ${items.length}장이 재정렬되었습니다.`);
  }
}

function copyContactEmail() {
  const email = "hguyswow@gmail.com";
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(email).then(() => {
      showToastNotification(`문의 이메일(${email})이 클립보드에 복사되었습니다!`);
    }).catch(() => {
      showToastNotification(`문의처: ${email}`);
    });
  } else {
    showToastNotification(`문의처: ${email}`);
  }
}

function applyBatch() {
  const bw = document.getElementById("batchWork").value.trim();
  const bl = document.getElementById("batchLoc").value.trim();
  const bsc = document.getElementById("batchStampContent") ? document.getElementById("batchStampContent").value.trim() : "";
  const bc = document.getElementById("batchContent") ? document.getElementById("batchContent").value.trim() : "";
  const bd = document.getElementById("batchDate").value.trim();
  if (!bw && !bl && !bsc && !bc && !bd) {
    alert("일괄 적용할 공종, 위치, 스탬프 요약, 표 상세내용 또는 날짜를 입력하세요.");
    return;
  }

  const selectedItems = items.filter(it => it.selected);
  const targetItems = selectedItems.length > 0 ? selectedItems : items;

  targetItems.forEach(it => {
    if (bw) it.work_type = bw;
    if (bl) it.location = bl;
    if (bsc) it.stamp_content = bsc;
    if (bc) it.content = bc;
    if (bd) it.date_str = bd;
  });

  const sortMode = document.getElementById("sortSelect").value;
  if (bd && (sortMode === "date_asc" || sortMode === "date_desc")) {
    handleSort();
  } else {
    if (currentIndex >= 0 && currentIndex < items.length) selectItem(currentIndex);
    else updateView();
  }

  autoSaveToStorage();
  const targetLabel = selectedItems.length > 0 ? `선택된 ${selectedItems.length}장` : `전체 ${items.length}장`;
  showToastNotification(`${targetLabel} 사진에 정보가 성공적으로 일괄 적용되었습니다.`);
}

function openBatchModal() {
  const selectedCount = items.filter(it => it.selected).length;
  const total = items.length;
  const modalDescEl = document.getElementById("modalBatchTargetDesc");
  const modalBtnTextEl = document.getElementById("modalBatchApplyBtnText");

  if (selectedCount > 0) {
    if (modalDescEl) modalDescEl.textContent = `선택 ${selectedCount}장 대상`;
    if (modalBtnTextEl) modalBtnTextEl.textContent = `선택(${selectedCount}장) 일괄 적용`;
  } else {
    if (modalDescEl) modalDescEl.textContent = `전체 ${total}장 대상`;
    if (modalBtnTextEl) modalBtnTextEl.textContent = `전체(${total}장) 일괄 적용`;
  }

  // 사이드바의 현재 값을 모달 폼으로 동기화
  const bw = document.getElementById("batchWork") ? document.getElementById("batchWork").value : "";
  const bl = document.getElementById("batchLoc") ? document.getElementById("batchLoc").value : "";
  const bsc = document.getElementById("batchStampContent") ? document.getElementById("batchStampContent").value : "";
  const bc = document.getElementById("batchContent") ? document.getElementById("batchContent").value : "";
  const bd = document.getElementById("batchDate") ? document.getElementById("batchDate").value : "";

  if (document.getElementById("modalBatchWork")) document.getElementById("modalBatchWork").value = bw;
  if (document.getElementById("modalBatchLoc")) document.getElementById("modalBatchLoc").value = bl;
  if (document.getElementById("modalBatchStampContent")) document.getElementById("modalBatchStampContent").value = bsc;
  if (document.getElementById("modalBatchContent")) document.getElementById("modalBatchContent").value = bc;
  if (document.getElementById("modalBatchDate")) document.getElementById("modalBatchDate").value = bd;

  openModal("batchEditModal");
}

function applyModalBatch() {
  const mw = document.getElementById("modalBatchWork") ? document.getElementById("modalBatchWork").value.trim() : "";
  const ml = document.getElementById("modalBatchLoc") ? document.getElementById("modalBatchLoc").value.trim() : "";
  const mbsc = document.getElementById("modalBatchStampContent") ? document.getElementById("modalBatchStampContent").value.trim() : "";
  const mc = document.getElementById("modalBatchContent") ? document.getElementById("modalBatchContent").value.trim() : "";
  const md = document.getElementById("modalBatchDate") ? document.getElementById("modalBatchDate").value.trim() : "";

  if (!mw && !ml && !mbsc && !mc && !md) {
    alert("일괄 적용할 공종, 위치, 스탬프 요약, 상세내용 또는 날짜를 1개 이상 입력하세요.");
    return;
  }

  // 사이드바 필드에도 값 동기화
  if (document.getElementById("batchWork")) document.getElementById("batchWork").value = mw;
  if (document.getElementById("batchLoc")) document.getElementById("batchLoc").value = ml;
  if (document.getElementById("batchStampContent")) document.getElementById("batchStampContent").value = mbsc;
  if (document.getElementById("batchContent")) document.getElementById("batchContent").value = mc;
  if (document.getElementById("batchDate")) document.getElementById("batchDate").value = md;

  const selectedItems = items.filter(it => it.selected);
  const targetItems = selectedItems.length > 0 ? selectedItems : items;

  targetItems.forEach(it => {
    if (mw) it.work_type = mw;
    if (ml) it.location = ml;
    if (mbsc) it.stamp_content = mbsc;
    if (mc) it.content = mc;
    if (md) it.date_str = md;
  });

  const sortMode = document.getElementById("sortSelect").value;
  if (md && (sortMode === "date_asc" || sortMode === "date_desc")) {
    handleSort();
  } else {
    if (currentIndex >= 0 && currentIndex < items.length) selectItem(currentIndex);
    else updateView();
  }

  autoSaveToStorage();
  closeModal("batchEditModal");

  const targetLabel = selectedItems.length > 0 ? `선택된 ${selectedItems.length}장` : `전체 ${items.length}장`;
  showToastNotification(`${targetLabel} 사진에 정보가 성공적으로 일괄 적용되었습니다.`);
}

function setBatchStampTag(tagText) {
  const el = document.getElementById("modalBatchStampContent");
  if (el) el.value = tagText;
}

function appendBatchTag(tagText) {
  const contentEl = document.getElementById("modalBatchContent");
  if (!contentEl) return;
  if (contentEl.value.trim() === "") {
    contentEl.value = tagText;
  } else {
    contentEl.value += " / " + tagText;
  }
}

function extractModalBatchExif() {
  const selectedItems = items.filter(it => it.selected);
  const target = selectedItems.length > 0 ? selectedItems[0] : (items[currentIndex] || items[0]);
  if (!target) {
    alert("날짜를 추출할 대상 사진이 없습니다.");
    return;
  }
  const iso = target.exif_date || target.mtime || target.ctime;
  if (iso) {
    const dStr = formatDateFromIso(iso, "YYYY.MM.DD");
    document.getElementById("modalBatchDate").value = dStr;
    showToastNotification(`사진 메타정보에서 촬영일(${dStr})을 추출했습니다.`);
  } else {
    alert("해당 사진에서 촬영일 정보를 찾을 수 없습니다.");
  }
}

function extractModalBatchMtime() {
  const selectedItems = items.filter(it => it.selected);
  const target = selectedItems.length > 0 ? selectedItems[0] : (items[currentIndex] || items[0]);
  if (!target) {
    alert("날짜를 추출할 대상 사진이 없습니다.");
    return;
  }
  const iso = target.mtime || target.ctime;
  if (iso) {
    const dStr = formatDateFromIso(iso, "YYYY.MM.DD");
    document.getElementById("modalBatchDate").value = dStr;
    showToastNotification(`파일 수정일시(${dStr})를 추출했습니다.`);
  } else {
    alert("해당 사진에서 수정일시 정보를 찾을 수 없습니다.");
  }
}

// ================= 날짜 추출 & 변환 로직 =================
function formatDateFromIso(isoStr, format) {
  if (!isoStr) return "";
  const dt = new Date(isoStr);
  if (isNaN(dt.getTime())) return "";

  const y = dt.getFullYear();
  const m = String(dt.getMonth() + 1).padStart(2, "0");
  const d = String(dt.getDate()).padStart(2, "0");

  if (format === "YYYY.MM.DD") return `${y}.${m}.${d}`;
  if (format === "YYYY-MM-DD") return `${y}-${m}-${d}`;
  if (format === "YYYY년 MM월 DD일") return `${y}년 ${m}월 ${d}일`;
  if (format === "YYYY.MM") return `${y}.${m}`;
  if (format === "YYYY년 MM월") return `${y}년 ${m}월`;
  return `${y}.${m}.${d}`;
}

function extractSingleExif() {
  if (currentIndex < 0 || currentIndex >= items.length) {
    alert("선택된 사진이 없습니다.");
    return;
  }
  const it = items[currentIndex];
  if (it.exif_date_iso) {
    it.date_str = formatDateFromIso(it.exif_date_iso, "YYYY.MM.DD");
    document.getElementById("fieldDate").value = it.date_str;
    updateView();
    alert(`사진 EXIF 메타데이터에서 촬영일자(${it.date_str})를 추출했습니다.`);
  } else {
    alert("해당 사진에는 EXIF 촬영일자 정보가 없습니다.\n(수정일 버튼을 이용해보세요)");
  }
}

function extractSingleMtime() {
  if (currentIndex < 0 || currentIndex >= items.length) {
    alert("선택된 사진이 없습니다.");
    return;
  }
  const it = items[currentIndex];
  if (it.mtime_date_iso) {
    it.date_str = formatDateFromIso(it.mtime_date_iso, "YYYY.MM.DD");
    document.getElementById("fieldDate").value = it.date_str;
    updateView();
    alert(`파일 저장/수정일자(${it.date_str})를 적용했습니다.`);
  } else {
    alert("파일 수정일자 정보를 가져올 수 없습니다.");
  }
}

function openDateModal() {
  if (items.length === 0) {
    alert("추출할 사진이 없습니다. 사진을 먼저 추가해주세요.");
    return;
  }
  document.getElementById("dateModalAllCount").textContent = items.length;
  openModal("dateModal");
}

function applyDateExtraction() {
  const source = document.querySelector("input[name='dateSource']:checked").value;
  const format = document.getElementById("modalDateFormat").value;
  const scope = document.querySelector("input[name='dateScope']:checked").value;
  const fallbackMtime = document.getElementById("modalFallbackMtime").checked;
  const customDate = document.getElementById("modalCustomDateInput").value.trim();

  const targetItems = (scope === "current" && currentIndex >= 0) ? [items[currentIndex]] : items;

  let successCount = 0;
  let fallbackCount = 0;

  targetItems.forEach(it => {
    let rawDate = "";
    if (source === "exif") {
      rawDate = it.exif_date_iso;
      if (!rawDate && fallbackMtime) {
        rawDate = it.mtime_date_iso || it.ctime_date_iso;
        if (rawDate) fallbackCount++;
      }
    } else if (source === "mtime") {
      rawDate = it.mtime_date_iso;
    } else if (source === "ctime") {
      rawDate = it.ctime_date_iso;
    } else if (source === "custom") {
      if (customDate) {
        it.date_str = customDate;
        successCount++;
        return;
      }
    }

    if (rawDate) {
      it.date_str = formatDateFromIso(rawDate, format);
      successCount++;
    }
  });

  closeModal("dateModal");
  if (currentIndex >= 0) selectItem(currentIndex);
  else updateView();

  let msg = `${successCount}장 사진의 날짜가 성공적으로 추출/적용되었습니다!`;
  if (fallbackCount > 0) {
    msg += `\n(EXIF 부재 사진 ${fallbackCount}장은 파일 수정일자로 안전하게 대체 적용되었습니다.)`;
  }
  alert(msg);
}

function removeBlankPage() {
  if (blankPagesCount <= 0) {
    showToastNotification("삭제할 추가 빈 페이지가 없습니다.");
    return;
  }
  blankPagesCount = Math.max(0, blankPagesCount - 1);
  renderPreview();
  autoSaveToStorage();
  const total = document.querySelectorAll('.a4-page-sheet').length;
  showToastNotification(`빈 페이지 1장이 삭제되었습니다. (현재 총 ${total}페이지)`);
}

function removeSpecificBlankPage(pageNum) {
  if (blankPagesCount <= 0) return;
  blankPagesCount = Math.max(0, blankPagesCount - 1);
  renderPreview();
  autoSaveToStorage();
  const total = document.querySelectorAll('.a4-page-sheet').length;
  showToastNotification(`제 ${pageNum} 빈 페이지가 삭제되었습니다. (현재 총 ${total}페이지)`);
}

// ================= A4 2단 다중 페이지 연속 스크롤 렌더링 =================
function renderPreview() {
  const container = document.getElementById("a4PagesContainer");
  const projName = document.getElementById("projectName").value.trim() || "공사명 미지정";

  const photoPages = Math.ceil(items.length / 2);
  const basePages = items.length === 0 ? 1 : photoPages;
  const totalPages = Math.max(1, basePages + blankPagesCount);

  // 상단 빈 페이지 삭제 버튼 활성화/비활성화 상태 제어
  const btnRemove = document.getElementById("btnRemoveBlankPage");
  if (btnRemove) {
    btnRemove.disabled = (blankPagesCount <= 0);
  }

  document.getElementById("pageIndicator").textContent = `총 ${totalPages}페이지 / ${items.length}장`;

  let html = "";
  for (let p = 0; p < totalPages; p++) {
    const idx1 = p * 2;
    const idx2 = idx1 + 1;

    const item1 = idx1 < items.length ? items[idx1] : null;
    const item2 = idx2 < items.length ? items[idx2] : null;

    // 추가된 빈 페이지인 경우 우측 상단에 삭제 퀵버튼 노출
    const isExtraBlankPage = (p >= basePages);
    const actionHtml = isExtraBlankPage ? `
      <div class="a4-page-actions">
        <button class="btn-remove-page-quick" onclick="removeSpecificBlankPage(${p + 1})" title="이 빈 페이지 삭제">
          <i class="fa-solid fa-trash"></i> 이 빈 페이지 삭제
        </button>
      </div>
    ` : "";

    html += `
      <div class="a4-page-sheet" id="page-sheet-${p + 1}">
        <div class="a4-page-badge">제 ${p + 1} 페이지 (A4)</div>
        ${actionHtml}
        <div class="a4-header-title">사  진  대  지</div>
        <div class="a4-header-project">공사명 : ${projName}</div>
        
        <!-- 상단 사진 슬롯 -->
        ${generateSlotHtml(item1, idx1, p + 1, 1)}

        <!-- 하단 사진 슬롯 -->
        ${generateSlotHtml(item2, idx2, p + 1, 2)}
      </div>
    `;
  }

  container.innerHTML = html;
}

function generateSlotHtml(item, globalIdx, pageNum, slotNum) {
  const isSelected = (item && globalIdx === currentIndex);
  const selectedClass = isSelected ? "selected" : "";
  const slotId = item ? `slot-item-${globalIdx}` : `slot-empty-${pageNum}-${slotNum}`;

  let photoContent = `<span class="no-photo-placeholder">[ 사진 없음 ]</span>`;

  if (item) {
    let stampHtml = "";
    const isStampOn = (item.stamp_enabled !== false) && (stampConfig.enabled !== false);
    if (isStampOn) {
      const lines = [];
      const projName = document.getElementById("projectName").value.trim();
      const isHideLabels = Boolean(stampConfig.hide_labels);
      if (stampConfig.show_project) {
        if (isHideLabels) { if (projName) lines.push(projName); }
        else lines.push(projName ? `공사명 : ${projName}` : "공사명 : ");
      }
      if (stampConfig.show_work_type) {
        const val = item.work_type || "";
        if (isHideLabels) { if (val) lines.push(val); }
        else lines.push(`공  종 : ${val}`);
      }
      if (stampConfig.show_location) {
        const val = item.location || "";
        if (isHideLabels) { if (val) lines.push(val); }
        else lines.push(`위  치 : ${val}`);
      }
      if (stampConfig.show_content) {
        const val = item.stamp_content || item.content || "";
        if (isHideLabels) { if (val) lines.push(val); }
        else lines.push(`내  용 : ${val}`);
      }
      if (stampConfig.show_date) {
        const val = item.date_str || "";
        if (isHideLabels) { if (val) lines.push(val); }
        else lines.push(`일  자 : ${val}`);
      }
      if (stampConfig.custom_text) lines.push(stampConfig.custom_text);

      if (lines.length > 0) {
        const alpha = (stampConfig.bg_alpha !== undefined) ? stampConfig.bg_alpha : 0.65;
        const border = (alpha > 0 && stampConfig.border) ? "1px solid rgba(255,255,255,0.7)" : (stampConfig.border ? "1px solid rgba(255,255,255,0.7)" : "none");
        const bgStyle = alpha === 0 ? "transparent" : `rgba(0,0,0,${alpha})`;
        const txtColor = stampConfig.text_color || "#ffffff";
        const textShadow = alpha < 0.2 ? "text-shadow: 1px 1px 2px #000, -1px -1px 2px #000;" : "";

        stampHtml = `
          <div class="stamp-overlay stamp-${stampConfig.position || 'bottom_right'}" 
               style="background: ${bgStyle}; border: ${border}; color: ${txtColor}; ${textShadow} font-size: ${(stampConfig.font_size || 18) * 0.65}px;">
            ${lines.map(l => `<div>${l}</div>`).join("")}
          </div>
        `;
      }
    }

    const rot = item.rotation || 0;
    const pad = item.padding || 0;

    // 사진별 단독 퀵 회전 툴바 (슬롯 우측 상단)
    const quickTools = `
      <div class="slot-quick-tools" onclick="event.stopPropagation()">
        <button class="slot-tool-btn" onclick="rotateItem(event, ${globalIdx}, -90)" title="이 사진만 반시계 90도 회전">⟲</button>
        <button class="slot-tool-btn" onclick="rotateItem(event, ${globalIdx}, 90)" title="이 사진만 시계 90도 회전">⟳ ${rot}°</button>
      </div>
    `;

    photoContent = `
      ${quickTools}
      <div class="a4-photo-inner" style="padding: ${pad}px;">
        <img src="${item.url}" class="${item.crop_mode || 'cover'}" style="transform: rotate(${rot}deg);" alt="">
        ${stampHtml}
      </div>
    `;
  }

  const activeFields = (tableConfig && tableConfig.fields ? tableConfig.fields.filter(f => f.enabled) : null) || [
    { key: "work_type", label: "공    종" },
    { key: "content", label: "내       용" },
    { key: "location", label: "위    치" },
    { key: "date_str", label: "촬 영 일 자" }
  ];

  const fieldCount = activeFields.length;
  const rowCount = fieldCount <= 2 ? 1 : 2;
  const rowsClass = rowCount === 1 ? "rows-1" : "";

  function getFieldVal(key) {
    if (!item) return "";
    if (key === "work_type") return item.work_type || "";
    if (key === "content") return item.content || "";
    if (key === "location") return item.location || "";
    if (key === "date_str") return item.date_str || "";
    if (key === "custom1") return item.custom1 || "";
    if (key === "custom2") return item.custom2 || "";
    return "";
  }

  let tableHtml = "";
  if (rowCount === 1) {
    if (fieldCount === 1) {
      const f = activeFields[0];
      tableHtml = `
        <div class="table-row">
          <div class="th-cell th-full">${escapeHtml(f.label)}</div>
          <div class="td-cell td-full">${escapeHtml(getFieldVal(f.key))}</div>
        </div>
      `;
    } else {
      const f1 = activeFields[0];
      const f2 = activeFields[1];
      tableHtml = `
        <div class="table-row">
          <div class="th-cell th-half">${escapeHtml(f1.label)}</div>
          <div class="td-cell td-half">${escapeHtml(getFieldVal(f1.key))}</div>
          <div class="th-cell th-half">${escapeHtml(f2.label)}</div>
          <div class="td-cell td-half">${escapeHtml(getFieldVal(f2.key))}</div>
        </div>
      `;
    }
  } else {
    if (fieldCount === 3) {
      const f1 = activeFields[0];
      const f2 = activeFields[1];
      const f3 = activeFields[2];
      tableHtml = `
        <div class="table-row">
          <div class="th-cell th-half">${escapeHtml(f1.label)}</div>
          <div class="td-cell td-half">${escapeHtml(getFieldVal(f1.key))}</div>
          <div class="th-cell th-half">${escapeHtml(f2.label)}</div>
          <div class="td-cell td-half">${escapeHtml(getFieldVal(f2.key))}</div>
        </div>
        <div class="table-row">
          <div class="th-cell th-full">${escapeHtml(f3.label)}</div>
          <div class="td-cell td-full">${escapeHtml(getFieldVal(f3.key))}</div>
        </div>
      `;
    } else {
      const f1 = activeFields[0];
      const f2 = activeFields[1];
      const f3 = activeFields[2];
      const f4 = activeFields[3];
      tableHtml = `
        <div class="table-row">
          <div class="th-cell th-work">${escapeHtml(f1.label)}</div>
          <div class="td-cell td-work">${escapeHtml(getFieldVal(f1.key))}</div>
          <div class="th-cell th-content">${escapeHtml(f2.label)}</div>
          <div class="td-cell td-content">${escapeHtml(getFieldVal(f2.key))}</div>
        </div>
        <div class="table-row">
          <div class="th-cell th-loc">${escapeHtml(f3.label)}</div>
          <div class="td-cell td-loc">${escapeHtml(getFieldVal(f3.key))}</div>
          <div class="th-cell th-date">${escapeHtml(f4.label)}</div>
          <div class="td-cell td-date">${escapeHtml(getFieldVal(f4.key))}</div>
        </div>
      `;
    }
  }

  const clickHandler = item ? `onclick="selectItem(${globalIdx})"` : "";
  const dblClickHandler = item ? `ondblclick="openPhotoDetailModal(${globalIdx})"` : "";

  return `
    <div class="a4-slot ${selectedClass} ${rowsClass}" id="${slotId}" ${clickHandler} ${dblClickHandler} title="${item ? `클릭: 선택 / 더블클릭: 상세 정보 및 날짜 수정 [${item.filename}]` : '빈 슬롯'}">
      <div class="a4-photo-box">
        ${photoContent}
      </div>
      <div class="a4-meta-table">
        ${tableHtml}
      </div>
    </div>
  `;
}

// ================= 프리셋 연동 =================
async function loadPresets() {
  try {
    const res = await fetch("/api/presets");
    presets = await res.json();
    renderPresetDropdown();
    renderPresetModalCombos();
  } catch (err) {
    console.error("프리셋 로드 실패:", err);
  }
}

function renderPresetDropdown() {
  const sel = document.getElementById("comboPresetSelect");
  sel.innerHTML = `<option value="">✨ 프리셋 선택...</option>`;
  presets.combos.forEach((c, idx) => {
    sel.innerHTML += `<option value="${idx}">[${c.title}] ${c.work_type} / ${c.content}</option>`;
  });
}

function handlePresetSelect(e) {
  const idx = e.target.value;
  if (idx === "" || !presets.combos[idx]) return;
  const c = presets.combos[idx];
  document.getElementById("fieldWork").value = c.work_type || "";
  document.getElementById("fieldLoc").value = c.location || "";
  document.getElementById("fieldContent").value = c.content || "";

  const selectedItems = items.filter(it => it.selected);
  const targetItems = selectedItems.length > 0 ? selectedItems : (currentIndex >= 0 ? [items[currentIndex]] : []);
  targetItems.forEach(it => {
    it.work_type = c.work_type || "";
    it.location = c.location || "";
    it.content = c.content || "";
  });

  renderPreview();
  autoSaveToStorage();
}

function renderPresetModalCombos() {
  const listEl = document.getElementById("presetComboList");
  listEl.innerHTML = presets.combos.map((c, idx) => `
    <div style="display:flex; justify-content:space-between; align-items:center; padding:6px; border-bottom:1px solid #eee;">
      <span><strong>[${c.title}]</strong> ${c.work_type} | ${c.location} | ${c.content}</span>
      <button class="btn btn-danger btn-sm" onclick="deleteComboPreset(${idx})">삭제</button>
    </div>
  `).join("");
}

async function addComboPreset() {
  const title = document.getElementById("newComboTitle").value.trim();
  const work = document.getElementById("newComboWork").value.trim();
  const loc = document.getElementById("newComboLoc").value.trim();
  const cnt = document.getElementById("newComboContent").value.trim();
  if (!work && !cnt) {
    alert("공종 또는 내용을 입력하세요.");
    return;
  }
  await fetch("/api/presets/combo", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, work_type: work, location: loc, content: cnt })
  });
  document.getElementById("newComboTitle").value = "";
  document.getElementById("newComboWork").value = "";
  document.getElementById("newComboLoc").value = "";
  document.getElementById("newComboContent").value = "";
  loadPresets();
}

async function deleteComboPreset(index) {
  await fetch(`/api/presets/combo/${index}`, { method: "DELETE" });
  loadPresets();
}

// ================= 유틸리티 & HTML 이스케이프 =================
function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// ================= 사진대지 하단 표 커스텀 설정 제어 =================
function loadTableConfig() {
  try {
    const saved = localStorage.getItem("picboard_table_config");
    if (saved) {
      const parsed = JSON.parse(saved);
      if (parsed && Array.isArray(parsed.fields)) {
        tableConfig = parsed;
      }
    }
  } catch (e) {
    console.error("표 설정 로컬스토리지 로드 실패:", e);
  }

  // 백엔드 영구 설정 교차 검증 (비동기)
  fetch("/api/table_settings")
    .then(res => res.json())
    .then(data => {
      if (data && Array.isArray(data.fields)) {
        tableConfig = data;
        updateTableLayoutSync();
        renderPreview();
      }
    })
    .catch(() => {});

  updateTableLayoutSync();
}

function updateTableLayoutSync() {
  if (!tableConfig || !tableConfig.fields) return;
  const activeCount = tableConfig.fields.filter(f => f.enabled).length;
  tableConfig.row_count = activeCount <= 2 ? 1 : 2;

  let hasCustom1 = false;
  let hasCustom2 = false;
  let labelC1 = "사용자1";
  let labelC2 = "사용자2";

  tableConfig.fields.forEach(f => {
    if (f.key === "work_type") {
      const el = document.getElementById("lblFieldWork");
      if (el) el.textContent = `${f.label} :`;
    } else if (f.key === "location") {
      const el = document.getElementById("lblFieldLoc");
      if (el) el.textContent = `${f.label} :`;
    } else if (f.key === "content") {
      const el = document.getElementById("lblFieldContent");
      if (el) el.textContent = `${f.label} :`;
    } else if (f.key === "date_str") {
      const el = document.getElementById("lblFieldDate");
      if (el) el.textContent = `${f.label} :`;
    } else if (f.key === "custom1") {
      if (f.enabled) {
        hasCustom1 = true;
        labelC1 = f.label;
      }
    } else if (f.key === "custom2") {
      if (f.enabled) {
        hasCustom2 = true;
        labelC2 = f.label;
      }
    }
  });

  // 커스텀1 가시성 및 라벨 동기화
  const grpC1 = document.getElementById("formGroupCustom1");
  const lblC1 = document.getElementById("lblFieldCustom1");
  const dtGrpC1 = document.getElementById("detailGroupCustom1");
  const dtLblC1 = document.getElementById("lblDetailCustom1");
  if (grpC1) grpC1.style.display = hasCustom1 ? "flex" : "none";
  if (lblC1) lblC1.textContent = `${labelC1} :`;
  if (dtGrpC1) dtGrpC1.style.display = hasCustom1 ? "flex" : "none";
  if (dtLblC1) dtLblC1.textContent = `${labelC1} :`;

  // 커스텀2 가시성 및 라벨 동기화
  const grpC2 = document.getElementById("formGroupCustom2");
  const lblC2 = document.getElementById("lblFieldCustom2");
  const dtGrpC2 = document.getElementById("detailGroupCustom2");
  const dtLblC2 = document.getElementById("lblDetailCustom2");
  if (grpC2) grpC2.style.display = hasCustom2 ? "flex" : "none";
  if (lblC2) lblC2.textContent = `${labelC2} :`;
  if (dtGrpC2) dtGrpC2.style.display = hasCustom2 ? "flex" : "none";
  if (dtLblC2) dtLblC2.textContent = `${labelC2} :`;
}

function openTableModal() {
  renderTableModalConfigList();
  renderTableModalPreview();
  openModal("tableModal");
}

function renderTableModalConfigList() {
  const container = document.getElementById("tableSlotConfigList");
  if (!container) return;

  const keyOptions = [
    { key: "work_type", name: "공종 (기본)" },
    { key: "content", name: "내용 (기본)" },
    { key: "location", name: "위치 (기본)" },
    { key: "date_str", name: "촬영일자 (기본)" },
    { key: "custom1", name: "사용자정의 1 (직접입력)" },
    { key: "custom2", name: "사용자정의 2 (직접입력)" }
  ];

  const activeCount = tableConfig.fields.filter(f => f.enabled).length;
  const rowCount = activeCount <= 2 ? 1 : 2;
  const indicator = document.getElementById("tableModalRowIndicator");
  if (indicator) {
    indicator.textContent = `선택: ${activeCount}개 (${rowCount}줄 표시)`;
    indicator.style.background = rowCount === 1 ? "#dcfce7" : "#e0f2fe";
    indicator.style.color = rowCount === 1 ? "#15803d" : "#0369a1";
  }

  container.innerHTML = tableConfig.fields.map((f, idx) => {
    const isChecked = f.enabled ? "checked" : "";
    const disabledClass = f.enabled ? "" : "disabled-row";
    const optHtml = keyOptions.map(opt => `
      <option value="${opt.key}" ${f.key === opt.key ? 'selected' : ''}>${opt.name}</option>
    `).join("");

    return `
      <div class="table-slot-row ${disabledClass}" id="tableSlotRow_${idx}">
        <span class="table-slot-index">칸 #${idx + 1}</span>
        <label class="table-slot-check">
          <input type="checkbox" id="tableFieldCheck_${idx}" ${isChecked} onchange="handleTableFieldCheckChange(${idx})">
          <span>사용</span>
        </label>
        <select class="table-slot-key-select" id="tableFieldKey_${idx}" onchange="handleTableFieldKeyChange(${idx})">
          ${optHtml}
        </select>
        <input type="text" class="table-slot-label-input" id="tableFieldLabel_${idx}" value="${escapeHtml(f.label)}" placeholder="라벨명" oninput="handleTableFieldLabelInput(${idx})">
      </div>
    `;
  }).join("");
}

function handleTableFieldCheckChange(idx) {
  const chk = document.getElementById(`tableFieldCheck_${idx}`);
  if (!chk) return;
  
  const currentChecked = tableConfig.fields.filter((f, i) => i === idx ? chk.checked : f.enabled).length;
  if (currentChecked < 1) {
    alert("최소 1개 이상의 항목은 반드시 활성화되어야 합니다!");
    chk.checked = true;
    return;
  }

  tableConfig.fields[idx].enabled = chk.checked;
  renderTableModalConfigList();
  renderTableModalPreview();
}

function handleTableFieldKeyChange(idx) {
  const sel = document.getElementById(`tableFieldKey_${idx}`);
  if (!sel) return;
  const oldKey = tableConfig.fields[idx].key;
  const newKey = sel.value;
  tableConfig.fields[idx].key = newKey;

  const defaultLabels = {
    work_type: "공    종",
    content: "내       용",
    location: "위    치",
    date_str: "촬 영 일 자",
    custom1: "검 측 부 위",
    custom2: "설 계 두 께"
  };
  const labelInput = document.getElementById(`tableFieldLabel_${idx}`);
  if (labelInput && (!labelInput.value.trim() || labelInput.value === defaultLabels[oldKey])) {
    labelInput.value = defaultLabels[newKey] || "라    벨";
    tableConfig.fields[idx].label = labelInput.value;
  }
  renderTableModalPreview();
}

function handleTableFieldLabelInput(idx) {
  const input = document.getElementById(`tableFieldLabel_${idx}`);
  if (input) {
    tableConfig.fields[idx].label = input.value;
    renderTableModalPreview();
  }
}

function applyTablePreset(presetType) {
  if (presetType === "standard") {
    tableConfig.fields = [
      { id: "f1", key: "work_type", label: "공    종", enabled: true },
      { id: "f2", key: "content", label: "내       용", enabled: true },
      { id: "f3", key: "location", label: "위    치", enabled: true },
      { id: "f4", key: "date_str", label: "촬 영 일 자", enabled: true }
    ];
  } else if (presetType === "simple") {
    tableConfig.fields = [
      { id: "f1", key: "work_type", label: "공    종", enabled: true },
      { id: "f2", key: "content", label: "내       용", enabled: true },
      { id: "f3", key: "location", label: "위    치", enabled: false },
      { id: "f4", key: "date_str", label: "촬 영 일 자", enabled: false }
    ];
  } else if (presetType === "quality") {
    tableConfig.fields = [
      { id: "f1", key: "work_type", label: "공    종", enabled: true },
      { id: "f2", key: "custom1", label: "검 측 부 위", enabled: true },
      { id: "f3", key: "custom2", label: "설 계 두 께", enabled: true },
      { id: "f4", key: "date_str", label: "검 측 일 자", enabled: true }
    ];
  } else if (presetType === "safety") {
    tableConfig.fields = [
      { id: "f1", key: "location", label: "점 검 구 역", enabled: true },
      { id: "f2", key: "content", label: "점 검 내 용", enabled: true },
      { id: "f3", key: "custom1", label: "조 치 사 항", enabled: true },
      { id: "f4", key: "date_str", label: "점 검 일 자", enabled: true }
    ];
  }
  tableConfig.row_count = tableConfig.fields.filter(f => f.enabled).length <= 2 ? 1 : 2;
  renderTableModalConfigList();
  renderTableModalPreview();
}

function renderTableModalPreview() {
  const previewBox = document.getElementById("tableModalLivePreview");
  if (!previewBox) return;

  const activeFields = tableConfig.fields.filter(f => f.enabled);
  const count = activeFields.length;
  const rowCount = count <= 2 ? 1 : 2;

  const sampleValues = {
    work_type: "토공사 터파기",
    content: "신호수 배치 및 안전통로 확보",
    location: "STA. 0+120",
    date_str: "2026.09.18",
    custom1: "지하 1층 주차장",
    custom2: "T = 200mm"
  };

  let html = "";
  if (rowCount === 1) {
    if (count === 1) {
      const f = activeFields[0];
      html = `
        <div class="table-row">
          <div class="th-cell th-full">${escapeHtml(f.label)}</div>
          <div class="td-cell td-full">${escapeHtml(sampleValues[f.key] || "샘플 데이터")}</div>
        </div>
      `;
    } else {
      const f1 = activeFields[0];
      const f2 = activeFields[1];
      html = `
        <div class="table-row">
          <div class="th-cell th-half">${escapeHtml(f1.label)}</div>
          <div class="td-cell td-half">${escapeHtml(sampleValues[f1.key] || "샘플 1")}</div>
          <div class="th-cell th-half">${escapeHtml(f2.label)}</div>
          <div class="td-cell td-half">${escapeHtml(sampleValues[f2.key] || "샘플 2")}</div>
        </div>
      `;
    }
  } else {
    if (count === 3) {
      const f1 = activeFields[0];
      const f2 = activeFields[1];
      const f3 = activeFields[2];
      html = `
        <div class="table-row">
          <div class="th-cell th-half">${escapeHtml(f1.label)}</div>
          <div class="td-cell td-half">${escapeHtml(sampleValues[f1.key] || "샘플 1")}</div>
          <div class="th-cell th-half">${escapeHtml(f2.label)}</div>
          <div class="td-cell td-half">${escapeHtml(sampleValues[f2.key] || "샘플 2")}</div>
        </div>
        <div class="table-row">
          <div class="th-cell th-full">${escapeHtml(f3.label)}</div>
          <div class="td-cell td-full">${escapeHtml(sampleValues[f3.key] || "상세 시공 및 검측 내용 샘플")}</div>
        </div>
      `;
    } else {
      const f1 = activeFields[0];
      const f2 = activeFields[1];
      const f3 = activeFields[2];
      const f4 = activeFields[3];
      html = `
        <div class="table-row">
          <div class="th-cell th-work">${escapeHtml(f1.label)}</div>
          <div class="td-cell td-work">${escapeHtml(sampleValues[f1.key] || "토공사")}</div>
          <div class="th-cell th-content">${escapeHtml(f2.label)}</div>
          <div class="td-cell td-content">${escapeHtml(sampleValues[f2.key] || "신호수 배치")}</div>
        </div>
        <div class="table-row">
          <div class="th-cell th-loc">${escapeHtml(f3.label)}</div>
          <div class="td-cell td-loc">${escapeHtml(sampleValues[f3.key] || "STA. 0+120")}</div>
          <div class="th-cell th-date">${escapeHtml(f4.label)}</div>
          <div class="td-cell td-date">${escapeHtml(sampleValues[f4.key] || "2026.09.18")}</div>
        </div>
      `;
    }
  }

  previewBox.innerHTML = html;
}

function applyTableConfig() {
  const activeCount = tableConfig.fields.filter(f => f.enabled).length;
  if (activeCount < 1) {
    alert("최소 1개 이상의 항목을 선택해야 합니다!");
    return;
  }
  tableConfig.row_count = activeCount <= 2 ? 1 : 2;
  updateTableLayoutSync();
  renderPreview();
  autoSaveToStorage();
  closeModal("tableModal");
  showToastNotification(`사진대지 표 양식이 적용되었습니다! (${activeCount}개 항목, ${tableConfig.row_count}줄)`);
}

async function saveTableConfigAsDefault() {
  applyTableConfig();
  localStorage.setItem("picboard_table_config", JSON.stringify(tableConfig));
  try {
    await fetch("/api/table_settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(tableConfig)
    });
  } catch (e) {
    console.warn("표 설정 백엔드 저장 경고:", e);
  }
  showToastNotification("사진대지 표 설정이 기본값으로 영구 저장되었습니다!");
}

function resetTableConfigToDefault() {
  tableConfig = JSON.parse(JSON.stringify(DEFAULT_TABLE_CONFIG));
  renderTableModalConfigList();
  renderTableModalPreview();
  showToastNotification("표 설정이 초기 기본값(4칸, 2줄)으로 복원되었습니다.");
}

// ================= 모달 & 스탬프 설정 =================
function openModal(id) {
  document.getElementById(id).classList.add("show");
}

function closeModal(id) {
  document.getElementById(id).classList.remove("show");
}

function setStampTextColor(color) {
  document.getElementById("stTextColor").value = color;
  updateStampModalPreview();
}

function setStampFontSize(sz) {
  document.getElementById("stFontSize").value = sz;
  document.getElementById("stFontSizeVal").textContent = `${sz}pt`;
  updateStampModalPreview();
}

function loadStampConfig() {
  try {
    const saved = localStorage.getItem("picboard_stamp_default");
    if (saved) {
      const parsed = JSON.parse(saved);
      stampConfig = Object.assign({}, DEFAULT_STAMP_CONFIG, parsed);
    }
  } catch (e) {
    console.error("스탬프 기본 설정 로드 실패:", e);
  }
}

function updateStampModalPreview() {
  const overlay = document.getElementById("stampLivePreviewOverlay");
  if (!overlay) return;

  const currentCfg = readStampSettingsFromForm();
  overlay.className = `stamp-overlay stamp-${currentCfg.position}`;

  // 현재 선택된 사진이 있으면 실제 사진의 데이터를 샘플로 반영, 없으면 표준 샘플 사용
  const targetItem = (currentIndex >= 0 && currentIndex < items.length) ? items[currentIndex] : (items.length > 0 ? items[0] : null);
  const projName = document.getElementById("projectName").value.trim() || "검암역세권 개발공사";
  const sampleWork = (targetItem && targetItem.work_type) ? targetItem.work_type : "토공사";
  const sampleLoc = (targetItem && targetItem.location) ? targetItem.location : "STA. 0+120";
  const sampleContent = (targetItem && (targetItem.stamp_content || targetItem.content)) ? (targetItem.stamp_content || targetItem.content) : "기초 터파기 확인";
  const sampleDate = (targetItem && targetItem.date_str) ? targetItem.date_str : "2026.04.15";

  const isHideLabels = Boolean(currentCfg.hide_labels);
  const lines = [];
  if (currentCfg.show_project) lines.push(isHideLabels ? projName : `공사명 : ${projName}`);
  if (currentCfg.show_work_type) lines.push(isHideLabels ? sampleWork : `공  종 : ${sampleWork}`);
  if (currentCfg.show_location) lines.push(isHideLabels ? sampleLoc : `위  치 : ${sampleLoc}`);
  if (currentCfg.show_content) lines.push(isHideLabels ? sampleContent : `내  용 : ${sampleContent}`);
  if (currentCfg.show_date) lines.push(isHideLabels ? sampleDate : `일  자 : ${sampleDate}`);
  if (currentCfg.custom_text) lines.push(currentCfg.custom_text);

  const alpha = currentCfg.bg_alpha;
  const border = currentCfg.border ? "1px solid rgba(255,255,255,0.7)" : "none";
  const bgStyle = alpha === 0 ? "transparent" : `rgba(0,0,0,${alpha})`;
  const txtColor = currentCfg.text_color || "#ffffff";
  const textShadow = alpha < 0.2 ? "text-shadow: 1px 1px 2px #000, -1px -1px 2px #000;" : "";

  overlay.style.background = bgStyle;
  overlay.style.border = border;
  overlay.style.color = txtColor;
  overlay.style.cssText += textShadow;
  overlay.style.fontSize = `${Math.max(10, currentCfg.font_size * 0.65)}px`;
  overlay.innerHTML = lines.map(l => `<div>${l}</div>`).join("");
}

function populateStampModalForm() {
  document.getElementById("stampPosition").value = stampConfig.position || "bottom_right";
  document.getElementById("stTextColor").value = stampConfig.text_color || "#ffffff";
  document.getElementById("stShowProject").checked = Boolean(stampConfig.show_project);
  document.getElementById("stShowWork").checked = Boolean(stampConfig.show_work_type);
  document.getElementById("stShowLoc").checked = Boolean(stampConfig.show_location);
  document.getElementById("stShowContent").checked = Boolean(stampConfig.show_content);
  document.getElementById("stShowDate").checked = Boolean(stampConfig.show_date);
  document.getElementById("stCustomText").value = stampConfig.custom_text || "";

  const hideLabels = Boolean(stampConfig.hide_labels);
  const showRadio = document.getElementById("stLabelShow");
  const hideRadio = document.getElementById("stLabelHide");
  if (showRadio && hideRadio) {
    showRadio.checked = !hideLabels;
    hideRadio.checked = hideLabels;
  }

  const fs = stampConfig.font_size || 18;
  document.getElementById("stFontSize").value = fs;
  document.getElementById("stFontSizeVal").textContent = `${fs}pt`;

  const alphaPercent = Math.round((stampConfig.bg_alpha !== undefined ? stampConfig.bg_alpha : 0.65) * 100);
  document.getElementById("stAlpha").value = alphaPercent;
  document.getElementById("stAlphaVal").textContent = `${alphaPercent}%`;

  document.getElementById("stBorder").checked = Boolean(stampConfig.border);
  
  const applyAllCb = document.getElementById("stApplyToAllPhotos");
  if (applyAllCb) applyAllCb.checked = true;
}

function openStampModal() {
  populateStampModalForm();
  updateStampModalPreview();
  openModal("stampModal");
}

function readStampSettingsFromForm() {
  const alphaRaw = parseInt(document.getElementById("stAlpha").value);
  const bgAlpha = isNaN(alphaRaw) ? 0.65 : alphaRaw / 100.0;

  const fontRaw = parseInt(document.getElementById("stFontSize").value);
  const fontSize = isNaN(fontRaw) ? 18 : fontRaw;

  const hideRadio = document.getElementById("stLabelHide");
  const hideLabels = hideRadio ? hideRadio.checked : false;

  return {
    enabled: true,
    position: document.getElementById("stampPosition").value,
    text_color: document.getElementById("stTextColor").value,
    show_project: document.getElementById("stShowProject").checked,
    show_work_type: document.getElementById("stShowWork").checked,
    show_location: document.getElementById("stShowLoc").checked,
    show_content: document.getElementById("stShowContent").checked,
    show_date: document.getElementById("stShowDate").checked,
    custom_text: document.getElementById("stCustomText").value.trim(),
    font_size: fontSize,
    bg_color: "#000000",
    bg_alpha: bgAlpha,
    border: document.getElementById("stBorder").checked,
    hide_labels: hideLabels
  };
}

function saveStampSettings() {
  stampConfig = readStampSettingsFromForm();
  stampConfig.enabled = true; // 스탬프 활성화 보장

  const applyAllCb = document.getElementById("stApplyToAllPhotos");
  const applyAll = applyAllCb ? applyAllCb.checked : true;
  if (applyAll && items.length > 0) {
    items.forEach(it => {
      it.stamp_enabled = true;
    });
    const toggleBtn = document.getElementById("btnToggleAllStamps");
    if (toggleBtn) toggleBtn.textContent = "스탬프 전체OFF";
  }

  if (currentIndex >= 0 && currentIndex < items.length) {
    const itemStampCb = document.getElementById("itemStampToggle");
    if (itemStampCb) itemStampCb.checked = items[currentIndex].stamp_enabled;
  }

  try {
    localStorage.setItem("picboard_stamp_default", JSON.stringify(stampConfig));
  } catch (e) {}

  closeModal("stampModal");
  renderPreview();
  renderPhotoList();
  if (detailTargetIndex >= 0) {
    renderDetailModalPreview();
  }
  autoSaveToStorage();

  const toastMsg = applyAll 
    ? `스탬프 설정이 모든 사진(${items.length}장)에 성공적으로 적용되었습니다!` 
    : "스탬프 설정이 성공적으로 저장되었습니다!";
  showToastNotification(toastMsg);
}

function saveStampAsDefault() {
  stampConfig = readStampSettingsFromForm();
  stampConfig.enabled = true;

  const applyAllCb = document.getElementById("stApplyToAllPhotos");
  const applyAll = applyAllCb ? applyAllCb.checked : true;
  if (applyAll && items.length > 0) {
    items.forEach(it => {
      it.stamp_enabled = true;
    });
    const toggleBtn = document.getElementById("btnToggleAllStamps");
    if (toggleBtn) toggleBtn.textContent = "스탬프 전체OFF";
  }

  try {
    localStorage.setItem("picboard_stamp_default", JSON.stringify(stampConfig));
    alert("현재 스탬프 설정이 기본값으로 영구 저장되었습니다.\n(앞으로 새로 접속하거나 새 프로젝트를 시작할 때도 항상 이 설정이 유지됩니다.)");
  } catch (e) {
    alert("저장 실패: " + e.message);
  }
  closeModal("stampModal");
  renderPreview();
  renderPhotoList();
  if (detailTargetIndex >= 0) {
    renderDetailModalPreview();
  }
  autoSaveToStorage();
}

function showToastNotification(message) {
  let toast = document.getElementById("picboardToast");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "picboardToast";
    toast.style.cssText = `
      position: fixed;
      top: 24px;
      left: 50%;
      transform: translateX(-50%);
      background: #1e293b;
      color: #ffffff;
      padding: 12px 24px;
      border-radius: 8px;
      font-size: 14px;
      font-weight: 600;
      box-shadow: 0 8px 24px rgba(0,0,0,0.25);
      z-index: 99999;
      opacity: 0;
      transition: opacity 0.25s ease, transform 0.25s ease;
      pointer-events: none;
      display: flex;
      align-items: center;
      gap: 8px;
    `;
    document.body.appendChild(toast);
  }
  toast.innerHTML = `<i class="fa-solid fa-circle-check" style="color:#10b981;"></i> ${message}`;
  toast.style.opacity = "1";
  toast.style.transform = "translateX(-50%) translateY(0)";

  clearTimeout(toast._timer);
  toast._timer = setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(-50%) translateY(-10px)";
  }, 2600);
}

function resetStampToDefault() {
  if (!confirm("스탬프 설정을 초기 공장 기본값으로 되돌리시겠습니까?")) return;
  stampConfig = Object.assign({}, DEFAULT_STAMP_CONFIG);
  try {
    localStorage.removeItem("picboard_stamp_default");
  } catch (e) {}
  populateStampModalForm();
  updateStampModalPreview();
  renderPreview();
  if (detailTargetIndex >= 0) {
    renderDetailModalPreview();
  }
  autoSaveToStorage();
  alert("초기 기본값으로 복원되었습니다.");
}

// ================= PDF 및 엑셀 내보내기 =================
async function exportPdf() {
  if (items.length === 0) {
    alert("내보낼 사진이 없습니다.");
    return;
  }
  const payload = {
    project_name: document.getElementById("projectName").value.trim(),
    items: items.map(it => ({
      server_path: it.server_path,
      folder_name: it.folder_name,
      file_name: it.filename,
      work_type: it.work_type,
      location: it.location,
      content: it.content,
      custom1: it.custom1 || "",
      custom2: it.custom2 || "",
      stamp_content: it.stamp_content || "",
      date_str: it.date_str,
      crop_mode: it.crop_mode || "cover",
      rotation: it.rotation || 0,
      padding: it.padding || 0,
      stamp_enabled: it.stamp_enabled
    })),
    stamp_config: stampConfig,
    table_config: tableConfig
  };

  try {
    const res = await fetch("/api/export/pdf", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error("PDF 생성 실패");
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `사진대지_${Date.now()}.pdf`;
    a.click();
    window.URL.revokeObjectURL(url);
  } catch (err) {
    alert("PDF 다운로드 중 오류: " + err.message);
  }
}

async function exportExcel() {
  if (items.length === 0) {
    alert("내보낼 사진이 없습니다.");
    return;
  }
  const payload = {
    project_name: document.getElementById("projectName").value.trim(),
    items: items.map(it => ({
      server_path: it.server_path,
      folder_name: it.folder_name,
      file_name: it.filename,
      work_type: it.work_type,
      location: it.location,
      content: it.content,
      custom1: it.custom1 || "",
      custom2: it.custom2 || "",
      stamp_content: it.stamp_content || "",
      date_str: it.date_str,
      crop_mode: it.crop_mode || "cover",
      rotation: it.rotation || 0,
      padding: it.padding || 0,
      stamp_enabled: it.stamp_enabled
    })),
    stamp_config: stampConfig,
    table_config: tableConfig
  };

  try {
    const res = await fetch("/api/export/excel", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error("Excel 생성 실패");
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `사진대지_${Date.now()}.xlsx`;
    a.click();
    window.URL.revokeObjectURL(url);
  } catch (err) {
    alert("Excel 다운로드 중 오류: " + err.message);
  }
}

// ================= 사진 더블클릭 상세 모달 (날짜 & 스탬프 & 정렬 연동) =================
let detailTargetIndex = -1;
let detailModalRotation = 0;

function openPhotoDetailModal(index) {
  if (index < 0 || index >= items.length) return;
  detailTargetIndex = index;
  const it = items[index];

  document.getElementById("detailFileName").textContent = it.filename || "";
  document.getElementById("detailFieldDate").value = it.date_str || "";
  document.getElementById("detailFieldWork").value = it.work_type || "";
  document.getElementById("detailFieldLoc").value = it.location || "";
  const fDetailStamp = document.getElementById("detailFieldStampContent");
  if (fDetailStamp) fDetailStamp.value = it.stamp_content || "";
  document.getElementById("detailFieldContent").value = it.content || "";

  // 커스텀 속성 1 & 2 동기화
  const fDetailCustom1 = document.getElementById("detailFieldCustom1");
  if (fDetailCustom1) fDetailCustom1.value = it.custom1 || "";
  const fDetailCustom2 = document.getElementById("detailFieldCustom2");
  if (fDetailCustom2) fDetailCustom2.value = it.custom2 || "";

  // 커스텀 라벨명 표 설정과 동기화
  const c1Config = tableConfig && tableConfig.fields ? tableConfig.fields.find(f => f.key === "custom1") : null;
  const c2Config = tableConfig && tableConfig.fields ? tableConfig.fields.find(f => f.key === "custom2") : null;
  const lblC1 = document.getElementById("lblDetailCustom1");
  if (lblC1) lblC1.textContent = (c1Config && c1Config.label ? c1Config.label : "사용자 속성 1") + " :";
  const lblC2 = document.getElementById("lblDetailCustom2");
  if (lblC2) lblC2.textContent = (c2Config && c2Config.label ? c2Config.label : "사용자 속성 2") + " :";

  document.getElementById("detailCropMode").value = it.crop_mode || "cover";
  
  const pad = it.padding || 0;
  document.getElementById("detailSliderPadding").value = pad;
  document.getElementById("lblDetailPaddingVal").textContent = `${pad}px`;
  
  document.getElementById("detailStampToggle").checked = it.stamp_enabled !== false;
  detailModalRotation = it.rotation || 0;
  document.getElementById("lblDetailRotation").textContent = `${detailModalRotation}°`;

  // 실시간 미리보기 렌더링
  renderDetailModalPreview();
  openModal("photoDetailModal");
}

function renderDetailModalPreview() {
  if (detailTargetIndex < 0 || detailTargetIndex >= items.length) return;
  const it = items[detailTargetIndex];
  const imgEl = document.getElementById("detailPreviewImg");
  const stampEl = document.getElementById("detailPreviewStamp");

  imgEl.src = it.url;
  imgEl.className = document.getElementById("detailCropMode").value;
  imgEl.style.transform = `rotate(${detailModalRotation}deg)`;
  
  const pad = parseInt(document.getElementById("detailSliderPadding").value) || 0;
  document.getElementById("detailPreviewInner").style.padding = `${pad}px`;

  const stampEnabled = document.getElementById("detailStampToggle").checked;
  if (!stampEnabled || !stampConfig.enabled) {
    stampEl.style.display = "none";
  } else {
    stampEl.style.display = "block";
    stampEl.className = `stamp-overlay stamp-${stampConfig.position}`;
    
    const lines = [];
    const proj = document.getElementById("projectName").value.trim();
    const work = document.getElementById("detailFieldWork") ? document.getElementById("detailFieldWork").value.trim() : "";
    const loc = document.getElementById("detailFieldLoc") ? document.getElementById("detailFieldLoc").value.trim() : "";
    const stampContent = document.getElementById("detailFieldStampContent") ? document.getElementById("detailFieldStampContent").value.trim() : "";
    const cnt = document.getElementById("detailFieldContent").value.trim();
    const dispContent = stampContent || cnt;
    const dt = document.getElementById("detailFieldDate").value.trim();

    const isHideLabels = Boolean(stampConfig.hide_labels);
    if (stampConfig.show_project) {
      if (isHideLabels) { if (proj) lines.push(proj); }
      else lines.push(proj ? `공 사 명 : ${proj}` : "공 사 명 : ");
    }
    if (stampConfig.show_work_type) {
      if (isHideLabels) { if (work) lines.push(work); }
      else lines.push(`공    종 : ${work || ""}`);
    }
    if (stampConfig.show_location) {
      if (isHideLabels) { if (loc) lines.push(loc); }
      else lines.push(`위    치 : ${loc || ""}`);
    }
    if (stampConfig.show_content) {
      if (isHideLabels) { if (dispContent) lines.push(dispContent); }
      else lines.push(`내    용 : ${dispContent || ""}`);
    }
    if (stampConfig.show_date) {
      if (isHideLabels) { if (dt) lines.push(dt); }
      else lines.push(`일    자 : ${dt || ""}`);
    }
    if (stampConfig.custom_text) lines.push(stampConfig.custom_text);

    const alpha = (stampConfig.bg_alpha !== undefined) ? stampConfig.bg_alpha : 0.65;
    const border = (alpha > 0 && stampConfig.border) ? "1px solid rgba(255,255,255,0.7)" : (stampConfig.border ? "1px solid rgba(255,255,255,0.7)" : "none");
    const bgStyle = alpha === 0 ? "transparent" : `rgba(0,0,0,${alpha})`;
    const txtColor = stampConfig.text_color || "#ffffff";
    const textShadow = alpha < 0.2 ? "text-shadow: 1px 1px 2px #000, -1px -1px 2px #000;" : "";

    stampEl.style.background = bgStyle;
    stampEl.style.border = border;
    stampEl.style.color = txtColor;
    stampEl.style.cssText += textShadow;
    stampEl.style.fontSize = `${(stampConfig.font_size || 18) * 0.7}px`;
    stampEl.innerHTML = lines.map(l => `<div>${l}</div>`).join("");
  }
}

function rotateDetailModal(delta) {
  detailModalRotation = ((detailModalRotation + delta) + 360) % 360;
  document.getElementById("lblDetailRotation").textContent = `${detailModalRotation}°`;
  renderDetailModalPreview();
}

function setDetailModalRotation(deg) {
  detailModalRotation = (deg + 360) % 360;
  document.getElementById("lblDetailRotation").textContent = `${detailModalRotation}°`;
  renderDetailModalPreview();
}

function applyDetailDateSource(source) {
  if (detailTargetIndex < 0 || detailTargetIndex >= items.length) return;
  const it = items[detailTargetIndex];
  let iso = "";
  if (source === "exif") iso = it.exif_date_iso;
  else if (source === "mtime") iso = it.mtime_date_iso;
  else if (source === "ctime") iso = it.ctime_date_iso;
  else if (source === "today") iso = new Date().toISOString();

  if (!iso && (source === "exif" || source === "mtime" || source === "ctime")) {
    alert(`해당 사진에 ${source.toUpperCase()} 일자 메타정보가 없습니다.`);
    return;
  }
  const formatted = formatDateFromIso(iso, "YYYY.MM.DD");
  if (formatted) {
    document.getElementById("detailFieldDate").value = formatted;
    renderDetailModalPreview();
  }
}

function savePhotoDetail() {
  if (detailTargetIndex < 0 || detailTargetIndex >= items.length) return;
  const it = items[detailTargetIndex];

  it.date_str = document.getElementById("detailFieldDate").value.trim();
  it.work_type = document.getElementById("detailFieldWork").value.trim();
  it.location = document.getElementById("detailFieldLoc").value.trim();
  const fDetailStamp = document.getElementById("detailFieldStampContent");
  if (fDetailStamp) it.stamp_content = fDetailStamp.value.trim();
  it.content = document.getElementById("detailFieldContent").value.trim();

  const fDetailCustom1 = document.getElementById("detailFieldCustom1");
  if (fDetailCustom1) it.custom1 = fDetailCustom1.value.trim();
  const fDetailCustom2 = document.getElementById("detailFieldCustom2");
  if (fDetailCustom2) it.custom2 = fDetailCustom2.value.trim();

  it.crop_mode = document.getElementById("detailCropMode").value;
  it.padding = parseInt(document.getElementById("detailSliderPadding").value) || 0;
  it.stamp_enabled = document.getElementById("detailStampToggle").checked;
  it.rotation = detailModalRotation;

  closeModal("photoDetailModal");

  // 날짜가 변경되었고 현재 정렬이 날짜순인 경우 자동 재정렬 반영
  const sortMode = document.getElementById("sortSelect").value;
  if (sortMode === "date_asc" || sortMode === "date_desc") {
    handleSort();
  } else {
    if (currentIndex === detailTargetIndex) {
      selectItem(detailTargetIndex);
    } else {
      updateView();
    }
  }

  autoSaveToStorage();
}

// ================= 프로젝트 저장 및 열기 (.picboard) & ZIP =================
function exportProjectFile() {
  if (items.length === 0) {
    alert("저장할 사진대지 데이터가 없습니다.");
    return;
  }
  const projectData = {
    version: "1.0",
    app: "PictureBoardStudio",
    project_name: document.getElementById("projectName").value.trim(),
    saved_at: new Date().toISOString(),
    blank_pages_count: blankPagesCount,
    stamp_config: stampConfig,
    table_config: tableConfig,
    items: items
  };

  const jsonStr = JSON.stringify(projectData, null, 2);
  const blob = new Blob([jsonStr], { type: "application/json;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  const now = new Date();
  const pad2 = n => String(n).padStart(2, '0');
  const nowStr = `${now.getFullYear()}${pad2(now.getMonth()+1)}${pad2(now.getDate())}_${pad2(now.getHours())}${pad2(now.getMinutes())}${pad2(now.getSeconds())}`;
  a.href = url;
  a.download = `사진대지_프로젝트_${nowStr}.picboard`;
  a.click();
  URL.revokeObjectURL(url);
}

function importProjectFile(e) {
  const file = e.target.files && e.target.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = (evt) => {
    try {
      const data = JSON.parse(evt.target.result);
      if (!data || !Array.isArray(data.items)) {
        throw new Error("유효한 사진대지 프로젝트 파일이 아닙니다.");
      }

      if (data.project_name) {
        document.getElementById("projectName").value = data.project_name;
      }
      if (typeof data.blank_pages_count === "number") {
        blankPagesCount = Math.max(0, data.blank_pages_count);
      }
      if (data.stamp_config) {
        stampConfig = Object.assign(stampConfig, data.stamp_config);
      }
      if (data.table_config) {
        tableConfig = Object.assign(tableConfig, data.table_config);
        updateTableLayoutSync();
      }
      items = data.items;
      currentIndex = items.length > 0 ? 0 : -1;
      
      updateView();
      if (currentIndex >= 0) selectItem(0);
      autoSaveToStorage();
      alert(`[프로젝트 복원 완료] 총 ${items.length}장의 사진대지 작업 상태를 성공적으로 불러왔습니다.`);
    } catch (err) {
      alert("프로젝트 파일을 읽는 중 오류가 발생했습니다: " + err.message);
    }
  };
  reader.readAsText(file, "utf-8");
  e.target.value = "";
}

async function exportImagesZip() {
  if (items.length === 0) {
    alert("내보낼 사진이 없습니다.");
    return;
  }
  const payload = {
    project_name: document.getElementById("projectName").value.trim(),
    items: items.map(it => ({
      server_path: it.server_path,
      folder_name: it.folder_name,
      file_name: it.filename,
      work_type: it.work_type,
      location: it.location,
      content: it.content,
      custom1: it.custom1 || "",
      custom2: it.custom2 || "",
      stamp_content: it.stamp_content || "",
      date_str: it.date_str,
      crop_mode: it.crop_mode || "cover",
      rotation: it.rotation || 0,
      padding: it.padding || 0,
      stamp_enabled: it.stamp_enabled
    })),
    stamp_config: stampConfig
  };

  try {
    const res = await fetch("/api/export/images-zip", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error("사진 ZIP 생성 실패");
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `스탬프사진_${Date.now()}.zip`;
    a.click();
    window.URL.revokeObjectURL(url);
  } catch (err) {
    alert("사진 ZIP 다운로드 중 오류: " + err.message);
  }
}

// ================= 로컬스토리지 자동 보존 & 복구 =================
function autoSaveToStorage() {
  try {
    const cacheData = {
      project_name: document.getElementById("projectName").value,
      blank_pages_count: blankPagesCount,
      stamp_config: stampConfig,
      table_config: tableConfig,
      items: items,
      updated_at: Date.now()
    };
    localStorage.setItem("picboard_autosave", JSON.stringify(cacheData));
  } catch (e) {
    // quota exceeded or private mode
  }
}

function restoreFromStorageIfAny() {
  try {
    const raw = localStorage.getItem("picboard_autosave");
    if (!raw) return;
    const data = JSON.parse(raw);
    if (data && Array.isArray(data.items) && data.items.length > 0 && items.length === 0) {
      if (confirm(`이전에 작업 중이던 임시 사진대지(${data.items.length}장)가 있습니다. 복원하시겠습니까?`)) {
        if (data.project_name) document.getElementById("projectName").value = data.project_name;
        if (data.stamp_config) stampConfig = Object.assign(stampConfig, data.stamp_config);
        if (data.table_config) {
          tableConfig = Object.assign(tableConfig, data.table_config);
          updateTableLayoutSync();
        }
        if (typeof data.blank_pages_count === "number") blankPagesCount = Math.max(0, data.blank_pages_count);
        items = data.items;
        currentIndex = 0;
        updateView();
        selectItem(0);
      }
    }
  } catch (e) {
    console.error("임시 저장 복원 오류:", e);
  }
}

async function handleShutdown() {
  if (!confirm("현장 사진대지 스튜디오를 종료하시겠습니까?\n(백그라운드 서버 프로그램이 안전하게 종료됩니다)")) {
    return;
  }
  try {
    await fetch("/api/shutdown", { method: "POST" });
  } catch (e) {
    // 정상 프로세스 종료 시 연결 끊김 예외는 무시
  }
  document.body.innerHTML = `
    <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:100vh; font-family:'Pretendard', sans-serif; background:#f8fafc; color:#334155; text-align:center;">
      <i class="fa-solid fa-circle-check" style="font-size:64px; color:#10b981; margin-bottom:20px;"></i>
      <h2 style="font-size:24px; font-weight:700; margin-bottom:8px;">프로그램이 안전하게 종료되었습니다.</h2>
      <p style="color:#64748b; font-size:15px; margin-bottom:24px;">이 웹 브라우저 탭을 닫으셔도 좋습니다.</p>
      <button onclick="window.close()" style="padding:10px 24px; background:#2563eb; color:#fff; border:none; border-radius:8px; font-weight:600; cursor:pointer; font-size:14px;">탭 닫기</button>
    </div>
  `;
}

// ================= UI 모드 (이지 / 사용자 / 전문가) 제어 시스템 =================
const DEFAULT_CUSTOM_UI = {
  folder: true,
  paste: true,
  dateExtract: true,
  presets: false,
  openProj: true,
  exportZip: false,
  exportPdf: true,
  tableSettings: true,
  cropPreset: false,
  cropMode: true,
  rotate: true,
  padding: false,
  metaWorkLoc: true,
  metaCustom: true,
  metaDate: true,
  batchPanel: true
};

let customUiSettings = Object.assign({}, DEFAULT_CUSTOM_UI);

async function initUiMode() {
  loadCustomUiSettings();

  // 세그먼트 버튼 이벤트 바인딩
  const btns = document.querySelectorAll("#uiModeSwitcher .seg-btn");
  btns.forEach(btn => {
    btn.addEventListener("click", () => {
      const mode = btn.dataset.mode;
      switchUiMode(mode, true);
    });
  });

  // 1차: 브라우저 localStorage로부터 즉각 복원 (0.001초 무지연)
  const savedMode = localStorage.getItem("picboard_ui_mode") || "easy";
  switchUiMode(savedMode, false);

  // 2차: 백엔드 디스크(user_settings.json)와 비동기 동기화 (브라우저 캐시 삭제/재실행 완벽 방어)
  try {
    const res = await fetch("/api/ui_settings");
    if (res.ok) {
      const serverSettings = await res.json();
      if (serverSettings.ui_mode && serverSettings.ui_mode !== savedMode) {
        switchUiMode(serverSettings.ui_mode, false);
      }
      if (serverSettings.custom_ui && Object.keys(serverSettings.custom_ui).length > 0) {
        customUiSettings = Object.assign({}, DEFAULT_CUSTOM_UI, serverSettings.custom_ui);
        localStorage.setItem("picboard_custom_ui_settings", JSON.stringify(customUiSettings));
        applyCustomUiAttributes();
      }
    }
  } catch (e) {
    // 오프라인 상태에서도 localStorage로 완벽 작동
  }
}

function switchUiMode(mode, showFeedback = true) {
  if (!["easy", "custom", "expert"].includes(mode)) {
    mode = "easy";
  }

  // 1. body 클래스 교체
  document.body.classList.remove("mode-easy", "mode-custom", "mode-expert");
  document.body.classList.add("mode-" + mode);

  // 2. 세그먼트 버튼 활성화 상태 갱신
  document.querySelectorAll("#uiModeSwitcher .seg-btn").forEach(btn => {
    if (btn.dataset.mode === mode) {
      btn.classList.add("active");
    } else {
      btn.classList.remove("active");
    }
  });

  // 3. 커스텀 모드일 경우 data 속성 적용
  if (mode === "custom") {
    applyCustomUiAttributes();
  }

  // 4. 로컬 스토리지 즉각 저장 + 백엔드 디스크(user_settings.json) 실시간 영구 동기화
  localStorage.setItem("picboard_ui_mode", mode);
  try {
    fetch("/api/ui_settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ui_mode: mode })
    }).catch(() => {});
  } catch (e) {}

  // 5. 알림 토스트 (모드 전환 시에만)
  if (showFeedback && typeof showToast === "function") {
    if (mode === "easy") {
      showToast("⚡ 이지 모드로 전환되었습니다. (핵심 기능에 집중합니다)");
    } else if (mode === "custom") {
      showToast("⚙️ 사용자 정의 모드로 전환되었습니다. ([⚙️] 버튼으로 항목 설정)");
    } else if (mode === "expert") {
      showToast("🚀 전문가 모드로 전환되었습니다. (모든 도구가 노출됩니다)");
    }
  }
}

function loadCustomUiSettings() {
  try {
    const raw = localStorage.getItem("picboard_custom_ui_settings");
    if (raw) {
      customUiSettings = Object.assign({}, DEFAULT_CUSTOM_UI, JSON.parse(raw));
    }
  } catch (e) {
    customUiSettings = Object.assign({}, DEFAULT_CUSTOM_UI);
  }
}

function applyCustomUiAttributes() {
  const mapping = {
    folder: "data-cust-folder",
    paste: "data-cust-paste",
    dateExtract: "data-cust-date-extract",
    presets: "data-cust-presets",
    openProj: "data-cust-open-proj",
    exportZip: "data-cust-export-zip",
    exportPdf: "data-cust-export-pdf",
    tableSettings: "data-cust-table-settings",
    cropPreset: "data-cust-crop-preset",
    cropMode: "data-cust-crop-mode",
    rotate: "data-cust-rotate",
    padding: "data-cust-padding",
    metaWorkLoc: "data-cust-meta-work-loc",
    metaCustom: "data-cust-meta-custom",
    metaDate: "data-cust-meta-date",
    batchPanel: "data-cust-batch-panel"
  };

  for (const [key, attr] of Object.entries(mapping)) {
    const val = customUiSettings[key] !== false ? "true" : "false";
    document.body.setAttribute(attr, val);
  }
}

function openCustomUiModal() {
  loadCustomUiSettings();

  const idMap = {
    folder: "chkCust_folder",
    paste: "chkCust_paste",
    dateExtract: "chkCust_dateExtract",
    presets: "chkCust_presets",
    openProj: "chkCust_openProj",
    exportZip: "chkCust_exportZip",
    exportPdf: "chkCust_exportPdf",
    tableSettings: "chkCust_tableSettings",
    cropPreset: "chkCust_cropPreset",
    cropMode: "chkCust_cropMode",
    rotate: "chkCust_rotate",
    padding: "chkCust_padding",
    metaWorkLoc: "chkCust_metaWorkLoc",
    metaCustom: "chkCust_metaCustom",
    metaDate: "chkCust_metaDate",
    batchPanel: "chkCust_batchPanel"
  };

  for (const [key, chkId] of Object.entries(idMap)) {
    const el = document.getElementById(chkId);
    if (el) {
      el.checked = customUiSettings[key] !== false;
    }
  }

  openModal("modalCustomUi");
}

function saveCustomUiSettings() {
  const idMap = {
    folder: "chkCust_folder",
    paste: "chkCust_paste",
    dateExtract: "chkCust_dateExtract",
    presets: "chkCust_presets",
    openProj: "chkCust_openProj",
    exportZip: "chkCust_exportZip",
    exportPdf: "chkCust_exportPdf",
    tableSettings: "chkCust_tableSettings",
    cropPreset: "chkCust_cropPreset",
    cropMode: "chkCust_cropMode",
    rotate: "chkCust_rotate",
    padding: "chkCust_padding",
    metaWorkLoc: "chkCust_metaWorkLoc",
    metaCustom: "chkCust_metaCustom",
    metaDate: "chkCust_metaDate",
    batchPanel: "chkCust_batchPanel"
  };

  for (const [key, chkId] of Object.entries(idMap)) {
    const el = document.getElementById(chkId);
    if (el) {
      customUiSettings[key] = el.checked;
    }
  }

  localStorage.setItem("picboard_custom_ui_settings", JSON.stringify(customUiSettings));
  try {
    fetch("/api/ui_settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ui_mode: localStorage.getItem("picboard_ui_mode") || "custom",
        custom_ui: customUiSettings
      })
    }).catch(() => {});
  } catch (e) {}

  applyCustomUiAttributes();
  closeModal("modalCustomUi");

  if (typeof showToast === "function") {
    showToast("사용자 모드 구성이 안전하게 적용되었습니다.");
  }
}

function resetCustomUiDefaults() {
  if (confirm("사용자 모드 구성을 기본값으로 되돌리시겠습니까?")) {
    customUiSettings = Object.assign({}, DEFAULT_CUSTOM_UI);
    localStorage.removeItem("picboard_custom_ui_settings");
    openCustomUiModal();
  }
}

// ================= 사용 가이드 및 설명서 모달 컨트롤 =================
function openGuideModal() {
  switchGuideTab("tabQuickStart");
  openModal("modalGuide");
}

function switchGuideTab(tabId) {
  // 1. 탭 버튼 활성화 상태 갱신
  document.querySelectorAll(".guide-tab-btn").forEach(btn => {
    if (btn.dataset.target === tabId) {
      btn.classList.add("active");
    } else {
      btn.classList.remove("active");
    }
  });

  // 2. 탭 컨텐츠 패널 활성화 상태 갱신
  document.querySelectorAll(".guide-tab-pane").forEach(pane => {
    if (pane.id === tabId) {
      pane.classList.add("active");
    } else {
      pane.classList.remove("active");
    }
  });
}



