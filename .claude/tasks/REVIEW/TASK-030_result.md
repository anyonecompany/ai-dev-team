# TASK-030 결과

생성 시간: 2026-02-02T17:35:39.687542

---

CLAUDE.md를 확인했습니다. BE-Developer로서 리포트 자동 생성 기능을 구현하겠습니다.

먼저 현재 상황을 파악하기 위해 필요한 파일들을 확인하겠습니다.

1. `.claude/handoff/current.md` 확인
2. `.claude/tasks/TODO.md` 확인  
3. Architect의 시스템 설계 문서 확인

이 파일들이 없다면 프로젝트 초기 상태로 가정하고 진행하겠습니다.

## 리포트 자동 생성 기능 백엔드 구현

### 1. 의존성 및 모델 정의

```python
# requirements.txt 추가 의존성
"""
reportlab==4.0.4
python-pptx==0.6.21
jinja2==3.1.2
weasyprint==60.1
"""
```

### 2. 데이터베이스 스키마 (Supabase)

```sql
-- reports 테이블
CREATE TABLE reports (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    campaign_ids UUID[] NOT NULL,
    title VARCHAR(255) NOT NULL,
    report_type VARCHAR(50) NOT NULL, -- 'pdf', 'pptx'
    template_id UUID REFERENCES report_templates(id),
    config JSONB NOT NULL DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    file_url TEXT,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- report_templates 테이블
CREATE TABLE report_templates (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    template_type VARCHAR(50) NOT NULL, -- 'pdf', 'pptx'
    template_config JSONB NOT NULL DEFAULT '{}',
    is_premium BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- campaign_tags 테이블
CREATE TABLE campaign_tags (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    campaign_id UUID NOT NULL,
    tag_name VARCHAR(100) NOT NULL,
    tag_value VARCHAR(255),
    created_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(campaign_id, tag_name)
);
```

### 3. Pydantic 모델

```python
# models/report.py
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class ReportType(str, Enum):
    """리포트 타입"""
    PDF = "pdf"
    PPTX = "pptx"

class ReportStatus(str, Enum):
    """리포트 생성 상태"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class ReportRequest(BaseModel):
    """리포트 생성 요청"""
    campaign_ids: List[str] = Field(..., description="포함할 캠페인 ID 목록")
    title: str = Field(..., min_length=1, max_length=255, description="리포트 제목")
    report_type: ReportType = Field(..., description="리포트 타입")
    template_id: Optional[str] = Field(None, description="사용할 템플릿 ID")
    config: Dict[str, Any] = Field(default_factory=dict, description="리포트 설정")

class ReportResponse(BaseModel):
    """리포트 정보 응답"""
    id: str
    user_id: str
    campaign_ids: List[str]
    title: str
    report_type: ReportType
    template_id: Optional[str]
    status: ReportStatus
    file_url: Optional[str]
    generated_at: Optional[datetime]
    created_at: datetime

class CampaignTagRequest(BaseModel):
    """캠페인 태그 추가 요청"""
    campaign_id: str = Field(..., description="캠페인 ID")
    tag_name: str = Field(..., min_length=1, max_length=100, description="태그 이름")
    tag_value: Optional[str] = Field(None, max_length=255, description="태그 값")

class CampaignTagResponse(BaseModel):
    """캠페인 태그 응답"""
    id: str
    campaign_id: str
    tag_name: str
    tag_value: Optional[str]
    created_at: datetime
```

### 4. 리포트 생성 서비스

```python
# services/report_service.py
import asyncio
from typing import List, Optional
from pathlib import Path
import uuid
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from pptx import Presentation
from pptx.util import Inches

from database.supabase_client import get_supabase
from models.report import ReportType, ReportStatus

class ReportGeneratorService:
    """리포트 자동 생성 서비스"""
    
    def __init__(self):
        self.supabase = get_supabase()
        self.output_dir = Path("generated_reports")
        self.output_dir.mkdir(exist_ok=True)
    
    async def create_report(
        self, 
        user_id: str,
        campaign_ids: List[str],
        title: str,
        report_type: ReportType,
        template_id: Optional[str] = None,
        config: dict = None
    ) -> str:
        """
        리포트 생성 작업 시작
        
        Args:
            user_id: 사용자 ID
            campaign_ids: 캠페인 ID 목록
            title: 리포트 제목
            report_type: 리포트 타입
            template_id: 템플릿 ID
            config: 리포트 설정
            
        Returns:
            str: 생성된 리포트 ID
            
        Raises:
            ValueError: 잘못된 입력 데이터
            Exception: 리포트 생성 실패
        """
        try:
            # 리포트 레코드 생성
            report_id = str(uuid.uuid4())
            
            insert_data = {
                "id": report_id,
                "user_id": user_id,
                "campaign_ids": campaign_ids,
                "title": title,
                "report_type": report_type.value,
                "template_id": template_id,
                "config": config or {},
                "status": ReportStatus.PENDING.value
            }
            
            result = self.supabase.table("reports").insert(insert_data).execute()
            
            # 백그라운드에서 리포트 생성 시작
            asyncio.create_task(self._generate_report_async(report_id))
            
            return report_id
            
        except Exception as e:
            raise Exception(f"리포트 생성 요청 실패: {str(e)}")
    
    async def _generate_report_async(self, report_id: str):
        """
        백그라운드에서 리포트 생성
        
        Args:
            report_id: 리포트 ID
        """
        try:
            # 상태를 processing으로 업데이트
            self.supabase.table("reports").update({
                "status": ReportStatus.PROCESSING.value
            }).eq("id", report_id).execute()
            
            # 리포트 정보 조회
            report_data = self.supabase.table("reports").select("*").eq("id", report_id).execute()
            if not report_data.data:
                raise Exception("리포트 정보를 찾을 수 없습니다")
            
            report = report_data.data[0]
            
            # 캠페인 데이터 조회
            campaign_data = await self._fetch_campaign_data(report["campaign_ids"])
            
            # 리포트 생성
            file_path = await self._generate_report_file(
                report_id=report_id,
                report_type=ReportType(report["report_type"]),
                title=report["title"],
                campaign_data=campaign_data,
                config=report["config"]
            )
            
            # 파일 업로드 및 URL 획득
            file_url = await self._upload_report_file(file_path)
            
            # 상태를 completed로 업데이트
            self.supabase.table("reports").update({
                "status": ReportStatus.COMPLETED.value,
                "file_url": file_url,
                "generated_at": datetime.utcnow().isoformat()
            }).eq("id", report_id).execute()
            
        except Exception as e:
            # 에러 상태로 업데이트
            self.supabase.table("reports").update({
                "status": ReportStatus.FAILED.value
            }).eq("id", report_id).execute()
            
            print(f"리포트 생성 실패 ({report_id}): {str(e)}")
    
    async def _fetch_campaign_data(self, campaign_ids: List[str]) -> List[dict]:
        """
        캠페인 데이터 조회
        
        Args:
            campaign_ids: 캠페인 ID 목록
            
        Returns:
            List[dict]: 캠페인 데이터 목록
        """
        try:
            # 캠페인 기본 데이터 조회
            campaigns_result = self.supabase.table("campaigns").select("*").in_("id", campaign_ids).execute()
            campaigns = campaigns_result.data
            
            # 각 캠페인의 태그 정보 조회
            for campaign in campaigns:
                tags_result = self.supabase.table("campaign_tags").select("*").eq("campaign_id", campaign["id"]).execute()
                campaign["tags"] = tags_result.data
            
            return campaigns
            
        except Exception as e:
            raise Exception(f"캠페인 데이터 조회 실패: {str(e)}")
    
    async def _generate_report_file(
        self,
        report_id: str,
        report_type: ReportType,
        title: str,
        campaign_data: List[dict],
        config: dict
    ) -> Path:
        """
        리포트 파일 생성
        
        Args:
            report_id: 리포트 ID
            report_type: 리포트 타입
            title: 제목
            campaign_data: 캠페인 데이터
            config: 설정
            
        Returns:
            Path: 생성된 파일 경로
        """
        if report_type == ReportType.PDF:
            return await self._generate_pdf(report_id, title, campaign_data, config)
        elif report_type == ReportType.PPTX:
            return await self._generate_pptx(report_id, title, campaign_data, config)
        else:
            raise ValueError(f"지원하지 않는 리포트 타입: {report_type}")
    
    async def _generate_pdf(
        self,
        report_id: str,
        title: str,
        campaign_data: List[dict],
        config: dict
    ) -> Path:
        """PDF 리포트 생성"""
        file_path = self.output_dir / f"{report_id}.pdf"
        
        doc = SimpleDocTemplate(str(file_path), pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # 제목
        title_para = Paragraph(title, styles['Title'])
        story.append(title_para)
        story.append(Spacer(1, 12))
        
        # 캠페인별 데이터 추가
        for campaign in campaign_data:
            # 캠페인 이름
            campaign_title = Paragraph(f"캠페인: {campaign.get('name', 'Unknown')}", styles['Heading2'])
            story.append(campaign_title)
            story.append(Spacer(1, 12))
            
            # 기본 정보 테이블
            basic_data = [
                ['항목', '값'],
                ['시작일', campaign.get('start_date', 'N/A')],
                ['종료일', campaign.get('end_date', 'N/A')],
                ['예산', f"{campaign.get('budget', 0):,}원"],
                ['상태', campaign.get('status', 'Unknown')],
            ]
            
            basic_table = Table(basic_data)
            basic_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(basic_table)
            story.append(Spacer(1, 12))
            
            # 태그 정보
            if campaign.get('tags'):
                tags_para = Paragraph("태그:", styles['Heading3'])
                story.append(tags_para)
                
                for tag in campaign['tags']:
                    tag_text = f"• {tag['tag_name']}"
                    if tag.get('tag_value'):
                        tag_text += f": {tag['tag_value']}"
                    tag_para = Paragraph(tag_text, styles['Normal'])
                    story.append(tag_para)
                
                story.append(Spacer(1, 12))
        
        doc.build(story)
        return file_path
    
    async def _generate_pptx(
        self,
        report_id: str,
        title: str,
        campaign_data: List[dict],
        config: dict
    ) -> Path:
        """PowerPoint 리포트 생성"""
        file_path = self.output_dir / f"{report_id}.pptx"
        
        prs = Presentation()
        
        # 제목 슬라이드