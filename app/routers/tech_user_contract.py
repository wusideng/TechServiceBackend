# 技师合约
import io
import aiohttp
from io import BytesIO
import os
from datetime import datetime, timedelta
import imghdr
from PIL import Image
from PyPDF2 import PageObject, PdfReader, PdfWriter  # 更新导入语句
import random
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from sqlalchemy.exc import IntegrityError
from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from sqlmodel import Session, select, not_
from typing import Optional

from config import product_base
from app.model.t_tech_user_contract import T_Tech_USER_Contract
from app.model.t_tech_user import T_Tech_User
from app.core.database import engine
from app.lib.utils.upload import (
    upload_file_to_cdn,
    upload_bytesio_to_cdn,
    upload_file_to_local,
)
from logger import logger

router = APIRouter(
    prefix="/techUserContract",
    tags=["techUserContract"],
    # dependencies=[Depends(get_sys_token_header)],
    # responses={404: {"description": "Not found"}},
)


@router.post("/")
async def create_tech_contract(tech_contract: T_Tech_USER_Contract):
    try:
        with Session(engine) as session:
            existing_user_auth = session.exec(
                select(T_Tech_USER_Contract).where(
                    T_Tech_USER_Contract.contracts_id == tech_contract.contracts_id
                )
            ).first()
            if existing_user_auth:
                raise HTTPException(
                    status_code=400,
                    detail="Item with this unique field already exists.",
                )
            else:
                session.add(tech_contract)
                session.commit()
                session.refresh(tech_contract)
                return {"msg": "create sucess", "data": tech_contract}
    except IntegrityError:
        raise HTTPException(status_code=401, detail="other error.")


# 商家入驻合作协议
@router.post("/signDealerContract")
async def sign_law_contract(
    tech_openid: str = Form(...),
    tech_name: str = Form(...),
    tech_card_id: str = Form(...),
    phone: str = Form(...),
    dealer_name: str = Form(...),
    dealer_phone: str = Form(...),
    dealer_owner_name: str = Form(...),
    dealer_owner_phone: str = Form(...),
    signature: UploadFile = File(None),
):
    signature_path = None  # 初始化变量
    if signature:
        signature_path = await upload_photo_to_cdn(signature, tech_openid, tech_name)
    # 生成合约PDF文件
    template_path = "cdn/商家入驻合作协议.pdf"  # 更新模板路径
    contract_pdf = await generate_dealer_contract_pdf(
        template_path,
        tech_name,
        tech_card_id,
        phone,
        dealer_name,
        dealer_phone,
        dealer_owner_name,
        dealer_owner_phone,
        signature,
    )
    # 上传合约文件到服务器CDN目录
    # contract_cdn_path = await upload_contract_to_server_io(contract_pdf, tech_openid, tech_name, '商家入驻合作协议')
    # print("上传成功服务器CDN:", contract_cdn_path)
    # 上传合约文件到CDN目录
    contract_cdn_path = await upload_contract_to_cdn_io(
        contract_pdf, tech_openid, tech_name, "商家入驻合作协议"
    )
    print("上传成功到七牛云CDN:", contract_cdn_path)
    # 创建并保存合约记录到数据库
    with Session(engine) as db:
        # 检查是否存在相同的合约
        existing_contract = (
            db.query(T_Tech_USER_Contract)
            .filter_by(tech_openid=tech_openid, contract_type="商家入驻合作协议")
            .first()
        )
        if existing_contract:
            # 如果存在，更新现有合约记录
            existing_contract.tech_name = tech_name
            existing_contract.tech_card_id = tech_card_id
            existing_contract.phone = phone
            existing_contract.dealer_name = dealer_name
            existing_contract.dealer_phone = dealer_phone
            existing_contract.dealer_owner_name = dealer_owner_name
            existing_contract.dealer_owner_phone = dealer_owner_phone
            existing_contract.signature = signature_path
            existing_contract.contract_file = contract_cdn_path
            existing_contract.status = "apply"
            existing_contract.status_desc = "申请中"
            db.commit()
            db.refresh(existing_contract)
            logger.info(
                "Contract %s updated successfully for technician %s",
                existing_contract,
                tech_openid,
            )
            return existing_contract
        else:
            # 如果不存在，新增合约记录
            contract = T_Tech_USER_Contract(
                tech_openid=tech_openid,
                tech_name=tech_name,
                tech_card_id=tech_card_id,
                phone=phone,
                signature=signature_path,
                contract_file=contract_cdn_path,
                contract_type="商家入驻合作协议",
                status_desc="申请中",
                status="apply",
            )
            db.add(contract)
            db.commit()
            db.refresh(contract)
            logger.info("Contract %s signed successfully for technician %s", contract)
            return contract


# 技师培训协议
@router.post("/signTrainingContract")
async def sign_law_contract(
    tech_openid: str = Form(...),
    dealer_name: str = Form(...),
    dealer_phone: str = Form(...),
    dealer_owner_name: str = Form(...),
    dealer_owner_phone: str = Form(...),
    dealer_owner_card_id: str = Form(...),
    signature: UploadFile = File(None),
):
    signature_path = None  # 初始化变量
    if signature:
        signature_path = await upload_photo_to_cdn(signature, tech_openid, dealer_name)
    # 生成合约PDF文件
    template_path = "cdn/技师培训协议.pdf"  # 更新模板路径
    contract_pdf = await generate_training_contract_pdf(
        template_path,
        dealer_name,
        dealer_phone,
        dealer_owner_name,
        dealer_owner_card_id,
        dealer_owner_phone,
        signature,
    )
    # 上传合约文件到服务器CDN目录
    # contract_cdn_path = await upload_contract_to_server_io(contract_pdf, tech_openid, dealer_name, '技师培训协议')
    # print("上传成功服务器CDN:", contract_cdn_path)
    # 上传合约文件到CDN目录
    contract_cdn_path = await upload_contract_to_cdn_io(
        contract_pdf, tech_openid, dealer_name, "技师培训协议"
    )
    print("上传成功到七牛云CDN:", contract_cdn_path)
    # 创建并保存合约记录到数据库
    with Session(engine) as db:
        # 检查是否存在相同的合约
        existing_contract = (
            db.query(T_Tech_USER_Contract)
            .filter_by(tech_openid=tech_openid, contract_type="技师培训协议")
            .first()
        )
        if existing_contract:
            # 如果存在，更新现有合约记录
            existing_contract.dealer_name = dealer_name
            existing_contract.dealer_phone = dealer_phone
            existing_contract.dealer_owner_name = dealer_owner_name
            existing_contract.dealer_owner_phone = dealer_owner_phone
            existing_contract.dealer_owner_card_id = dealer_owner_card_id
            existing_contract.signature = signature_path
            existing_contract.contract_file = contract_cdn_path
            existing_contract.status = "apply"
            existing_contract.status_desc = "申请中"
            db.commit()
            db.refresh(existing_contract)
            logger.info(
                "Contract %s updated successfully for technician %s",
                existing_contract,
                tech_openid,
            )
            return existing_contract
        else:
            # 如果不存在，新增合约记录
            contract = T_Tech_USER_Contract(
                tech_openid=tech_openid,
                dealer_name=dealer_name,
                dealer_phone=dealer_phone,
                dealer_owner_card_id=dealer_owner_card_id,
                dealer_owner_name=dealer_owner_name,
                dealer_owner_phone=dealer_owner_phone,
                signature=signature_path,
                contract_file=contract_cdn_path,
                contract_type="技师培训协议",
                status_desc="申请中",
                status="apply",
            )
            db.add(contract)
            db.commit()
            db.refresh(contract)
            logger.info("Contract %s signed successfully for technician %s", contract)
            return contract


# 遵纪守法承诺书
@router.post("/signLawContract")
async def sign_law_contract(
    tech_openid: str = Form(...),
    tech_name: str = Form(...),
    tech_card_id: str = Form(...),
    phone: str = Form(...),
    signature: UploadFile = File(None),
):
    signature_path = None  # 初始化变量
    if signature:
        signature_path = await upload_photo_to_cdn(signature, tech_openid, tech_name)
    # 生成合约PDF文件
    template_path = "cdn/遵纪守法承诺书.pdf"  # 更新模板路径
    contract_pdf = await generate_law_contract_pdf(
        template_path, tech_name, tech_card_id, phone, signature
    )
    # 上传合约文件到服务器CDN目录
    # contract_cdn_path = await upload_contract_to_server_io(contract_pdf, tech_openid, tech_name, '遵纪守法承诺书')
    # print("上传成功服务器CDN:", contract_cdn_path)
    # 上传合约文件到CDN目录
    contract_cdn_path = await upload_contract_to_cdn_io(
        contract_pdf, tech_openid, tech_name, "遵纪守法承诺书"
    )
    print("上传成功到七牛云CDN:", contract_cdn_path)
    # 创建并保存合约记录到数据库
    with Session(engine) as db:
        # 检查是否存在相同的合约
        existing_contract = (
            db.query(T_Tech_USER_Contract)
            .filter_by(tech_openid=tech_openid, contract_type="遵纪守法承诺书")
            .first()
        )
        if existing_contract:
            # 如果存在，更新现有合约记录
            existing_contract.tech_name = tech_name
            existing_contract.tech_card_id = tech_card_id
            existing_contract.phone = phone
            existing_contract.signature = signature_path
            existing_contract.contract_file = contract_cdn_path
            existing_contract.status = "apply"
            existing_contract.status_desc = "申请中"
            db.commit()
            db.refresh(existing_contract)
            logger.info(
                "Contract %s updated successfully for technician %s",
                existing_contract,
                tech_openid,
            )
            return existing_contract
        else:
            # 如果不存在，新增合约记录
            contract = T_Tech_USER_Contract(
                tech_openid=tech_openid,
                tech_name=tech_name,
                tech_card_id=tech_card_id,
                phone=phone,
                signature=signature_path,
                contract_file=contract_cdn_path,
                contract_type="遵纪守法承诺书",
                status_desc="申请中",
                status="apply",
            )
            db.add(contract)
            db.commit()
            db.refresh(contract)
            logger.info("Contract %s signed successfully for technician %s", contract)
            return contract


# 肖像权许可使用协议,技师端签约
@router.post("/signPortraitContract")
async def sign_portrait_contract(
    tech_openid: str = Form(...),
    tech_name: str = Form(...),
    tech_sex: str = Form(...),
    phone: str = Form(...),
    photo_front: UploadFile = File(None),
    photo_back: UploadFile = File(None),  # 可选字段
    signature: UploadFile = File(None),
):
    photo_front_path = None  # 初始化变量
    photo_back_path = None  # 初始化变量
    signature_path = None  # 初始化变量

    # 检查并保存上传的文件
    if photo_front:
        photo_front_path = await upload_photo_to_cdn(
            photo_front, tech_openid, tech_name
        )
        print(photo_front_path)
    if photo_back:
        photo_back_path = await upload_photo_to_cdn(photo_back, tech_openid, tech_name)
        print(photo_back_path)
    if signature:
        signature_path = await upload_photo_to_cdn(signature, tech_openid, tech_name)
        print(signature_path)

    # 检查是否所有必需文件都已上传
    if not all([photo_front_path, photo_back_path, signature_path]):
        logger.warning("Missing one or more required files to generate contract PDF")
        return {"error": "Missing required files"}

    # 生成合约PDF文件
    template_path = "cdn/肖像权许可使用协议.pdf"  # 更新模板路径
    contract_pdf = await generate_portrait_contract_pdf(
        template_path, tech_name, tech_sex, phone, photo_front, photo_back, signature
    )
    logger.info("Contract PDF generated successfully")
    # 上传合约文件到服务器CDN目录
    # contract_cdn_path = await upload_contract_to_server_io(contract_pdf, tech_openid, tech_name, "肖像权许可使用协议")
    # print("上传成功服务器CDN:", contract_cdn_path)
    # 上传合约文件到CDN目录
    contract_cdn_path = await upload_contract_to_cdn_io(
        contract_pdf, tech_openid, tech_name, "肖像权许可使用协议"
    )
    print("上传肖像权许可使用协议成功到七牛云CDN:", tech_name, tech_openid, contract_cdn_path)
    # 创建并保存合约记录到数据库
    with Session(engine) as db:
        # 检查是否存在相同的合约
        existing_contract = (
            db.query(T_Tech_USER_Contract)
            .filter_by(tech_openid=tech_openid, contract_type="肖像权许可使用协议")
            .first()
        )
        if existing_contract:
            # 如果存在，更新现有合约记录
            existing_contract.tech_name = tech_name
            existing_contract.tech_sex = tech_sex
            existing_contract.phone = phone
            existing_contract.photo_front = photo_front_path
            existing_contract.photo_back = photo_back_path
            existing_contract.signature = signature_path
            existing_contract.contract_file = contract_cdn_path
            existing_contract.status = "apply"
            db.commit()
            db.refresh(existing_contract)
            logger.info(
                "Contract %s updated successfully for technician %s",
                existing_contract,
                tech_openid,
            )
            return existing_contract
        else:
            # 如果不存在，新增合约记录
            contract = T_Tech_USER_Contract(
                tech_openid=tech_openid,
                tech_name=tech_name,
                tech_sex=tech_sex,
                phone=phone,
                photo_front=photo_front_path,
                photo_back=photo_back_path,
                signature=signature_path,
                contract_file=contract_cdn_path,
                contract_type="肖像权许可使用协议",
                status="apply",
            )
            db.add(contract)
            db.commit()
            db.refresh(contract)
            logger.info("Contract %s signed successfully for technician %s", contract)
            return contract


# 肖像权许可使用协议，管理端盖章审核
@router.post("/reviewContract")
async def review_contract(
    tech_openid: str = Form(...),
    contract_type: str = Form(...),
    status: str = Form(...),
    status_desc: Optional[str] = Form(...),
):
    print(contract_type)
    with Session(engine) as db:
        contract = db.exec(
            select(T_Tech_USER_Contract).where(
                T_Tech_USER_Contract.tech_openid == tech_openid,
                T_Tech_USER_Contract.contract_type == contract_type,
            )
        ).first()
        if not contract:
            return "Contract not found"
        contract.status = status
        file_path = contract.contract_file  # 更新模板路径
        seal_path = "cdn/seal_dq.png"
        tech_name = contract.tech_name
        contract_pdf = None
        if contract_type == "肖像权许可使用协议":
            contract_pdf = await review_portrait_contract_pdf(file_path, seal_path)
        elif contract_type == "遵纪守法承诺书":
            contract_pdf = await review_law_contract_pdf(file_path, seal_path)
        elif contract_type == "技师培训协议":
            contract_pdf = await review_training_contract_pdf(file_path, seal_path)
            # 技师培训协议是商户与公司签订，所以没有技师信息
            tech_name = contract.dealer_name
        elif contract_type == "商家入驻合作协议":
            contract_pdf = await review_dealer_contract_pdf(file_path, seal_path)
        if not contract_pdf:
            return "Failed to generate contract PDF"
        # 上传合约文件到服务器CDN目录
        # contract_cdn_path = await upload_contract_to_server_io(contract_pdf, tech_openid, tech_name, contract_type)
        # print("上传成功服务器CDN:", contract_cdn_path)
        # 上传合约文件到CDN目录
        contract_cdn_path = await upload_contract_to_cdn_io(
            contract_pdf, tech_openid, tech_name, contract_type
        )
        logger.info("审核证书", tech_openid, tech_name, contract_type)
        contract.contract_file = contract_cdn_path
        contract.status = status
        contract.status_desc = status_desc
        contract.update_time = datetime.now()
        db.add(contract)
        db.commit()
        db.refresh(contract)
        return contract


@router.get("/")
async def read_contract():
    with Session(engine) as db:
        contracts = db.exec(select(T_Tech_USER_Contract)).all()
        return contracts


# 只查看已申请，未签约的技师
# 申请上线审批通过的的技师，才有工作电话work_phone
@router.get("/TechStatus")
async def read_contract():
    with Session(engine) as db:
        contracts = (
            select(T_Tech_User, T_Tech_USER_Contract)
            .join(
                T_Tech_USER_Contract,
                T_Tech_USER_Contract.tech_openid == T_Tech_User.openid,
                isouter=True,
            )
            .where(
                # not_(
                #     T_Tech_User.openid.like("%Mock%")
                #     | T_Tech_User.openid.like("%mock%")
                # ),
                T_Tech_User.work_phone != "",
                T_Tech_User.work_phone != "string",
            )
            .order_by(T_Tech_USER_Contract.contracts_id.desc())
        )
        results = db.exec(contracts).all()
        # 拼接返回信息
        combined_results = []
        for user, contract in results:
            combined_info = {
                "user_id": user.user_id,
                "user_nickname": user.user_nickname,
                "user_openid": user.openid,
                "user_phone": user.user_phone,
                "user_city": user.user_city,
                "photo_work": user.photo_work,
                "user_sex": user.user_sex,
                "contract_id": contract.contracts_id if contract else None,
                "status": contract.status if contract else "No contract",
                "contract_type": contract.contract_type if contract else "No contract",
                "created_time": contract.created_time if contract else "No contract",
                "contract_file": contract.contract_file if contract else "No contract",
            }
            combined_results.append(combined_info)
        return combined_results


@router.get("/statusByTech/{tech_openid}/{contract_type}/")
async def read_contract_by_openid(tech_openid: str, contract_type: str):
    with Session(engine) as db:
        contract = db.exec(
            select(T_Tech_USER_Contract)
            .where(
                T_Tech_USER_Contract.tech_openid == tech_openid,
                T_Tech_USER_Contract.contract_type == contract_type,
            )
            .order_by(T_Tech_USER_Contract.contracts_id.desc())
        ).first()
        if not contract:
            return "Contract not found"
        return contract


# contract_type = ”肖像权许可使用协议“, ”遵纪守法承诺书“，“技师培训协议”，“商家入驻合作协议”
@router.get("/statusByTechAndType/{tech_openid}/")
async def read_contract_by_openid_and_type(tech_openid: str, contract_type: str):
    with Session(engine) as db:
        contract = db.exec(
            select(T_Tech_USER_Contract)
            .where(
                T_Tech_USER_Contract.tech_openid == tech_openid,
                T_Tech_USER_Contract.contract_type == contract_type,
            )
            .order_by(T_Tech_USER_Contract.contracts_id.desc())
        ).first()
        if not contract:
            return "Contract not found"
        return contract


# 商家入驻合租协议盖章（管理端）
async def review_dealer_contract_pdf(file_path: str, seal_path: str):
    # https 转化成http协议
    http_path = file_path.replace("https://", "http://")
    # 注册支持汉字的字体
    chinese_font_path = "cdn/Arial Unicode.ttf"  # 替换为实际的字体文件路径
    pdfmetrics.registerFont(TTFont("ChineseFont", chinese_font_path))
    # 将cdn件内容存储在 BytesIO 对象中
    async with aiohttp.ClientSession() as session:
        async with session.get(http_path) as response:
            if response.status != 200:
                raise Exception(f"Failed to download file from CDN: {response.status}")
            file_content = await response.read()
    file_stream = io.BytesIO(file_content)
    # 加载模板内容
    template_pdf = PdfReader(file_stream)
    pdf_writer = PdfWriter()
    page1 = template_pdf.pages[0]
    page2 = template_pdf.pages[1]
    page3 = template_pdf.pages[2]
    page4 = template_pdf.pages[3]
    page5 = template_pdf.pages[4]

    content = page5.extract_text()
    # print(content)
    if content:
        # 盖章日期
        packet = BytesIO()
        canvas_api = canvas.Canvas(packet, pagesize=letter)
        canvas_api.setFont("ChineseFont", 12)  #
        # A4 的尺寸为 595 points x 842 points。文本在坐标第一象限，所以坐标是 (0, 0)
        current_date = datetime.now().strftime("%Y年%m月%d日")
        canvas_api.drawString(150, 300, current_date)
        canvas_api.save()
        packet.seek(0)
    # 添加日期
    new_pdf = PdfReader(packet)
    page5 = template_pdf.pages[4]
    # 添加签章图片
    await add_seal_image_to_pdf(seal_path, page5, 135, 300, (100, 100))
    page5.merge_page(new_pdf.pages[0])

    pdf_writer.add_page(page1)
    pdf_writer.add_page(page2)
    pdf_writer.add_page(page3)
    pdf_writer.add_page(page4)
    pdf_writer.add_page(page5)
    output_pdf = BytesIO()
    pdf_writer.write(output_pdf)
    output_pdf.seek(0)
    return output_pdf


# 技师培训协议盖章（管理端）
async def review_training_contract_pdf(file_path: str, seal_path: str):
    # https 转化成http协议
    http_path = file_path.replace("https://", "http://")
    # 注册支持汉字的字体
    chinese_font_path = "cdn/Arial Unicode.ttf"  # 替换为实际的字体文件路径
    pdfmetrics.registerFont(TTFont("ChineseFont", chinese_font_path))
    # 将cdn件内容存储在 BytesIO 对象中
    async with aiohttp.ClientSession() as session:
        async with session.get(http_path) as response:
            if response.status != 200:
                raise Exception(f"Failed to download file from CDN: {response.status}")
            file_content = await response.read()
    file_stream = io.BytesIO(file_content)
    # 加载模板内容
    template_pdf = PdfReader(file_stream)
    pdf_writer = PdfWriter()
    page1 = template_pdf.pages[0]
    page2 = template_pdf.pages[1]
    # 添加签章图片
    await add_seal_image_to_pdf(seal_path, page2, 165, 395, (100, 100))
    content = page2.extract_text()
    # print(content)
    if content:
        # 盖章日期
        packet = BytesIO()
        canvas_api = canvas.Canvas(packet, pagesize=letter)
        canvas_api.setFont("ChineseFont", 12)  #
        # A4 的尺寸为 595 points x 842 points。文本在坐标第一象限，所以坐标是 (0, 0)
        current_date = datetime.now().strftime("%Y年%m月%d日")
        canvas_api.drawString(125, 395, current_date)
        canvas_api.save()
        packet.seek(0)
    # 添加日期
    new_pdf = PdfReader(packet)
    page2 = template_pdf.pages[1]

    page2.merge_page(new_pdf.pages[0])

    pdf_writer.add_page(page1)
    pdf_writer.add_page(page2)
    output_pdf = BytesIO()
    pdf_writer.write(output_pdf)
    output_pdf.seek(0)
    return output_pdf


# 遵纪守法承诺书盖章（管理端）
async def review_law_contract_pdf(file_path: str, seal_path: str):
    # https 转化成http协议
    http_path = file_path.replace("https://", "http://")
    # 注册支持汉字的字体
    chinese_font_path = "cdn/Arial Unicode.ttf"  # 替换为实际的字体文件路径
    pdfmetrics.registerFont(TTFont("ChineseFont", chinese_font_path))
    # 将cdn件内容存储在 BytesIO 对象中
    async with aiohttp.ClientSession() as session:
        async with session.get(http_path) as response:
            if response.status != 200:
                raise Exception(f"Failed to download file from CDN: {response.status}")
            file_content = await response.read()
    file_stream = io.BytesIO(file_content)
    # 加载模板内容
    template_pdf = PdfReader(file_stream)
    pdf_writer = PdfWriter()
    page = template_pdf.pages[0]
    content = page.extract_text()
    if content:
        # 盖章日期
        packet = BytesIO()
        canvas_api = canvas.Canvas(packet, pagesize=letter)
        canvas_api.setFont("ChineseFont", 12)  #
        # A4 的尺寸为 595 points x 842 points。文本在坐标第一象限，所以坐标是 (0, 0)
        current_date = datetime.now().strftime("%Y年%m月%d日")
        canvas_api.drawString(125, 95, current_date)
        canvas_api.save()
        packet.seek(0)
    # 添加日期
    new_pdf = PdfReader(packet)
    page = template_pdf.pages[0]
    page.merge_page(new_pdf.pages[0])
    # 添加签章图片
    await add_seal_image_to_pdf(seal_path, page, 125, 95, (100, 100))
    page.merge_page(new_pdf.pages[0])
    pdf_writer.add_page(page)
    output_pdf = BytesIO()
    pdf_writer.write(output_pdf)
    output_pdf.seek(0)
    return output_pdf


# 肖像权使用协议盖章（管理端）
async def review_portrait_contract_pdf(file_path: str, seal_path: str):
    # 注册支持汉字的字体
    chinese_font_path = "cdn/Arial Unicode.ttf"  # 替换为实际的字体文件路径
    pdfmetrics.registerFont(TTFont("ChineseFont", chinese_font_path))
    # 将cdn件内容存储在 BytesIO 对象中
    async with aiohttp.ClientSession() as session:
        async with session.get(file_path) as response:
            if response.status != 200:
                raise Exception(f"Failed to download file from CDN: {response.status}")
            file_content = await response.read()
    file_stream = io.BytesIO(file_content)
    # 加载模板内容
    template_pdf = PdfReader(file_stream)
    pdf_writer = PdfWriter()
    page = template_pdf.pages[0]
    content = page.extract_text()
    if content:
        # 盖章日期
        packet = BytesIO()
        canvas_api = canvas.Canvas(packet, pagesize=letter)
        canvas_api.setFont("ChineseFont", 12)  #
        # A4 的尺寸为 595 points x 842 points。文本在坐标第一象限，所以坐标是 (0, 0)
        current_date = datetime.now().strftime("%Y年%m月%d日")
        canvas_api.drawString(125, 95, current_date)
        canvas_api.save()
        packet.seek(0)
    # 添加日期
    new_pdf = PdfReader(packet)
    page = template_pdf.pages[0]
    page.merge_page(new_pdf.pages[0])
    # 添加签章图片
    await add_seal_image_to_pdf(seal_path, page, 125, 95, (100, 100))
    page.merge_page(new_pdf.pages[0])
    pdf_writer.add_page(page)
    output_pdf = BytesIO()
    pdf_writer.write(output_pdf)
    output_pdf.seek(0)
    return output_pdf


# 商家入驻合作协议
async def generate_dealer_contract_pdf(
    template_path: str,
    tech_name: str,
    tech_card_id: str,
    phone: str,
    dealer_name: str,
    dealer_phone: str,
    dealer_owner_name: str,
    dealer_owner_phone: str,
    signature: UploadFile = None,
):
    # 字体配置
    CHINESE_FONT_PATH = "cdn/Arial Unicode.ttf"
    FONT_SIZE = 12
    pdfmetrics.registerFont(TTFont("ChineseFont", CHINESE_FONT_PATH))
    # A4 的尺寸为 595 points x 842 points。文本在坐标第一象限，所以坐标是 (0, 0)
    # 坐标配置
    PAGE1_COORDS = {
        "dealer_name": (135, 662),
        "dealer_phone": (320, 662),
        "dealer_owner_name": (138, 638),
        "dealer_owner_phone": (323, 638),
        "tech_name": (360, 289),
        "tech_phone": (387, 270),
        "tech_card_id": (155, 270),
        "date_begin": (182, 100),
        "date_end": (318, 100),
    }
    PAGE4_COORDS = {"dealer_name": (170, 150), "dealer_phone": (300, 150)}
    PAGE5_COORDS = {
        "dealer_name": (335, 465),
        "date": (340, 300),
        "signature": (385, 370, (80, 50)),
    }

    template_pdf = PdfReader(template_path)
    pdf_writer = PdfWriter()
    # 处理第一页
    page1 = template_pdf.pages[0]
    packet = BytesIO()
    canvas_api = canvas.Canvas(packet, pagesize=letter)
    canvas_api.setFont("ChineseFont", FONT_SIZE)
    canvas_api.drawString(*PAGE1_COORDS["dealer_name"], dealer_name)
    canvas_api.drawString(*PAGE1_COORDS["dealer_phone"], dealer_phone)
    canvas_api.drawString(*PAGE1_COORDS["dealer_owner_name"], dealer_owner_name)
    canvas_api.drawString(*PAGE1_COORDS["dealer_owner_phone"], dealer_owner_phone)
    canvas_api.drawString(*PAGE1_COORDS["tech_name"], tech_name)
    canvas_api.drawString(*PAGE1_COORDS["tech_phone"], phone)
    canvas_api.drawString(*PAGE1_COORDS["tech_card_id"], tech_card_id)
    current_date = datetime.now()
    formatted_current_date = current_date.strftime("%Y年%m月%d日")
    one_year_later = current_date.replace(year=current_date.year + 1)
    formatted_one_year_later = one_year_later.strftime("%Y年%m月%d日")
    canvas_api.drawString(*PAGE1_COORDS["date_begin"], formatted_current_date)
    canvas_api.drawString(*PAGE1_COORDS["date_end"], formatted_one_year_later)
    canvas_api.save()
    packet.seek(0)
    page1.merge_page(PdfReader(packet).pages[0])
    # 处理第二页
    page2 = template_pdf.pages[1]
    # 处理第三页
    page3 = template_pdf.pages[2]
    # 处理第四页
    page4 = template_pdf.pages[3]
    packet = BytesIO()
    canvas_api = canvas.Canvas(packet, pagesize=letter)
    canvas_api.setFont("ChineseFont", FONT_SIZE)
    canvas_api.drawString(*PAGE4_COORDS["dealer_name"], dealer_name)
    canvas_api.drawString(*PAGE4_COORDS["dealer_phone"], dealer_phone)
    canvas_api.save()
    packet.seek(0)
    page4.merge_page(PdfReader(packet).pages[0])

    # 处理第五页
    page5 = template_pdf.pages[4]
    packet = BytesIO()
    canvas_api = canvas.Canvas(packet, pagesize=letter)
    canvas_api.setFont("ChineseFont", FONT_SIZE)
    canvas_api.drawString(*PAGE5_COORDS["dealer_name"], dealer_name)
    current_date = datetime.now().strftime("%Y年%m月%d日")
    canvas_api.drawString(*PAGE5_COORDS["date"], current_date)
    canvas_api.save()
    packet.seek(0)
    page5.merge_page(PdfReader(packet).pages[0])

    if signature:
        await add_image_to_pdf(
            signature,
            page5,
            PAGE5_COORDS["signature"][0],
            PAGE5_COORDS["signature"][1],
            PAGE5_COORDS["signature"][2],
        )

    pdf_writer.add_page(page1)
    pdf_writer.add_page(page2)
    pdf_writer.add_page(page3)
    pdf_writer.add_page(page4)
    pdf_writer.add_page(page5)

    output_pdf = BytesIO()
    pdf_writer.write(output_pdf)
    output_pdf.seek(0)
    return output_pdf


# 技师培训协议,技师端生成合同
async def generate_training_contract_pdf(
    template_path: str,
    dealer_name: str,
    dealer_phone: str,
    dealer_owner_name: str,
    dealer_owner_card_id: str,
    dealer_owner_phone: str,
    signature: UploadFile = None,
):

    # 字体配置
    CHINESE_FONT_PATH = "cdn/Arial Unicode.ttf"
    FONT_SIZE = 12
    pdfmetrics.registerFont(TTFont("ChineseFont", CHINESE_FONT_PATH))

    # 坐标配置
    PAGE1_COORDS = {
        "dealer_name": (138, 663),
        "dealer_phone": (350, 663),
        "dealer_owner_name": (139, 640),
        "dealer_owner_card_id": (370, 640),
        "dealer_owner_phone": (165, 615),
    }

    PAGE2_COORDS = {"date": (368, 396), "signature": (385, 425, (80, 50))}

    try:
        template_pdf = PdfReader(template_path)
        pdf_writer = PdfWriter()

        # 处理第一页
        page1 = template_pdf.pages[0]
        packet = BytesIO()
        canvas_api = canvas.Canvas(packet, pagesize=letter)
        canvas_api.setFont("ChineseFont", FONT_SIZE)
        canvas_api.drawString(*PAGE1_COORDS["dealer_name"], dealer_name)
        canvas_api.drawString(*PAGE1_COORDS["dealer_phone"], dealer_phone)
        canvas_api.drawString(*PAGE1_COORDS["dealer_owner_name"], dealer_owner_name)
        canvas_api.drawString(
            *PAGE1_COORDS["dealer_owner_card_id"], dealer_owner_card_id
        )
        canvas_api.drawString(*PAGE1_COORDS["dealer_owner_phone"], dealer_owner_phone)
        canvas_api.save()
        packet.seek(0)
        page1.merge_page(PdfReader(packet).pages[0])

        # 处理第二页
        page2 = template_pdf.pages[1]
        packet = BytesIO()
        canvas_api = canvas.Canvas(packet, pagesize=letter)
        canvas_api.setFont("ChineseFont", FONT_SIZE)
        current_date = datetime.now().strftime("%Y年%m月%d日")
        canvas_api.drawString(*PAGE2_COORDS["date"], current_date)
        canvas_api.save()
        packet.seek(0)
        page2.merge_page(PdfReader(packet).pages[0])
        if signature:
            await add_image_to_pdf(
                signature,
                page2,
                PAGE2_COORDS["signature"][0],
                PAGE2_COORDS["signature"][1],
                PAGE2_COORDS["signature"][2],
            )

        pdf_writer.add_page(page1)
        pdf_writer.add_page(page2)

        output_pdf = BytesIO()
        pdf_writer.write(output_pdf)
        output_pdf.seek(0)
        return output_pdf

    except Exception as e:
        logger.error(f"Failed to generate training contract: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate contract")


# 遵纪守法承诺书,技师端生成合同
async def generate_law_contract_pdf(
    template_path: str,
    tech_name: str,
    tech_card_id: str,
    phone: str,
    signature: UploadFile = None,
):
    # 注册支持汉字的字体
    chinese_font_path = "cdn/Arial Unicode.ttf"  # 替换为实际的字体文件路径
    pdfmetrics.registerFont(TTFont("ChineseFont", chinese_font_path))

    # 加载模板内容
    template_pdf = PdfReader(template_path)
    pdf_writer = PdfWriter()
    # pdf_writer.add_page(template_pdf.pages[0])
    # 获取模板页面的内容
    page = template_pdf.pages[0]
    content = page.extract_text()
    print(content)
    if content:
        # 创建新页面添加修改后的文本和额外信息
        packet = BytesIO()
        canvas_api = canvas.Canvas(packet, pagesize=letter)
        canvas_api.setFont("ChineseFont", 12)  #
        # A4 的尺寸为 595 points x 842 points。文本在坐标第一象限，所以坐标是 (0, 0)
        canvas_api.drawString(395, 240, tech_name)
        canvas_api.drawString(395, 216, tech_card_id)
        canvas_api.drawString(395, 193, phone)
        print("phone", phone)
        current_date = datetime.now().strftime("%Y年%m月%d日")
        canvas_api.drawString(368, 102, current_date)
        canvas_api.save()
        packet.seek(0)

    new_pdf = PdfReader(packet)
    page = template_pdf.pages[0]
    page.merge_page(new_pdf.pages[0])
    await add_image_to_pdf(signature, page, 355, 120, (80, 50))
    pdf_writer.add_page(page)
    output_pdf = BytesIO()
    pdf_writer.write(output_pdf)
    output_pdf.seek(0)
    return output_pdf


# 肖像权许可协议,技师端生成合同
async def generate_portrait_contract_pdf(
    template_path: str,
    tech_name: str,
    tech_sex: str,
    phone: str,
    photo_front: UploadFile = None,
    photo_back: UploadFile = None,
    signature: UploadFile = None,
):
    # 注册支持汉字的字体
    chinese_font_path = "cdn/Arial Unicode.ttf"  # 替换为实际的字体文件路径
    pdfmetrics.registerFont(TTFont("ChineseFont", chinese_font_path))

    # 加载模板内容
    template_pdf = PdfReader(template_path)
    pdf_writer = PdfWriter()
    # pdf_writer.add_page(template_pdf.pages[0])
    # 获取模板页面的内容
    page = template_pdf.pages[0]
    content = page.extract_text()
    print(content)
    if content:
        # 创建新页面添加修改后的文本和额外信息
        packet = BytesIO()
        canvas_api = canvas.Canvas(packet, pagesize=letter)
        canvas_api.setFont("ChineseFont", 12)  #
        # A4 的尺寸为 595 points x 842 points。文本在坐标第一象限，所以坐标是 (0, 0)
        canvas_api.drawString(150, 690, "尚阳科技")
        canvas_api.drawString(150, 670, tech_name)
        canvas_api.drawString(280, 670, tech_sex)
        canvas_api.drawString(380, 670, phone)
        current_date = datetime.now().strftime("%Y年%m月%d日")
        canvas_api.drawString(368, 95, current_date)
        canvas_api.save()
        packet.seek(0)

    new_pdf = PdfReader(packet)
    page = template_pdf.pages[0]
    page.merge_page(new_pdf.pages[0])

    await add_image_to_pdf(photo_front, page, 97, 200, (190, 110))
    await add_image_to_pdf(photo_back, page, 317, 200, (190, 110))
    await add_image_to_pdf(signature, page, 355, 120, (80, 50))
    pdf_writer.add_page(page)
    output_pdf = BytesIO()
    pdf_writer.write(output_pdf)
    output_pdf.seek(0)
    return output_pdf


def convert_png_to_jpeg_bytesio(png_bytesio, quality=90):
    """
    将包含PNG内容的BytesIO对象转换为包含JPEG内容的BytesIO对象

    参数:
        png_bytesio: io.BytesIO对象，包含PNG文件内容
        quality: int, JPEG质量 (1-100)

    返回:
        io.BytesIO对象，包含JPEG格式的文件内容
    """
    # 确保流位置在开始处
    png_bytesio.seek(0)

    # 打开PNG图像
    image = Image.open(png_bytesio)

    # 处理透明度
    if image.mode in ("RGBA", "LA") or (
        image.mode == "P" and "transparency" in image.info
    ):
        background = Image.new("RGB", image.size, (255, 255, 255))
        if image.mode == "P":
            image = image.convert("RGBA")
        background.paste(image, mask=image.split()[3] if image.mode == "RGBA" else None)
        image = background
    elif image.mode != "RGB":
        image = image.convert("RGB")

    # 创建新的BytesIO对象
    jpeg_bytesio = io.BytesIO()

    # 保存为JPEG
    image.save(jpeg_bytesio, format="JPEG", quality=quality)

    # 重置流位置
    jpeg_bytesio.seek(0)

    # 返回BytesIO对象
    return jpeg_bytesio


async def upload_photo_to_cdn(photo: UploadFile, user_id: str, user_nickname: str):
    photo_filename = (
        "Tech_User_"
        + user_id
        + "_"
        + user_nickname
        + "_"
        + str(random.randint(1, 100))
        + photo.filename
    )
    upload_cdn_folder_path = "uploads"
    cdn_path = await upload_file_to_cdn(photo, upload_cdn_folder_path, photo_filename)
    return cdn_path


async def upload_contract_to_cdn_io(
    contract_file: io.BytesIO, user_id: str, user_nickname: str, file_type: str
):
    contract_filename = (
        file_type
        + "_"
        + user_id
        + "_"
        + user_nickname
        + "_"
        + str(random.randint(1, 1000))
        + "_"
        + "contract.pdf"
    )
    upload_cdn_folder_path = "uploads"
    cdn_path = await upload_bytesio_to_cdn(
        contract_file, upload_cdn_folder_path, contract_filename
    )
    return cdn_path


async def upload_contract_to_server_io(
    contract_file: io.BytesIO, user_id: str, user_nickname: str, file_type: str
):
    print("upload_contract_to_server_io")
    print(random.randint(1, 100))
    print(file_type, user_id, user_nickname)

    contract_filename = (
        file_type
        + "_"
        + user_id
        + "_"
        + user_nickname
        + "_"
        + str(random.randint(1, 1000))
        + "_"
        + "contract.pdf"
    )
    print("contract_filename:", contract_file)
    # 初始化 local_dir
    local_dir = None
    server_cdn = None
    # 判断 product_base 的值并赋值 local_dir
    if product_base == "http://127.0.0.1:8000":
        local_dir = os.path.dirname(
            "/Volumes/T7/尚阳工作室/到家服务平台开发/code-backend/cdn/"
        )
        server_cdn = "http://127.0.0.1:8000/cdn/"
    elif product_base == "https://visualstreet.cn/apidev":
        local_dir = "C:\\workspace\\dev\\backend\\cdn\\"
        server_cdn = "https://visualstreet.cn/apidev/cdn/"
    elif product_base == "https://visualstreet.cn/api/cdn/":
        local_dir = "C:\\workspace\\prod\\backend\\cdn\\"
        server_cdn = "https://visualstreet.cn/apidev/cdn/"
    # C:\workspace\dev\backend\cdn
    if not os.path.exists(local_dir):
        os.makedirs(local_dir)
    local_path = os.path.join(local_dir, contract_filename)
    with open(local_path, "wb") as f:
        f.write(contract_file.getvalue())
    server_cdn_path = server_cdn + contract_filename
    return server_cdn_path


# 加盖公章
async def add_seal_image_to_pdf(
    file_path: str,
    page: PageObject,
    pos_x: int,
    pos_y: int,
    size: tuple,
):
    # 打开文件并获取文件对象
    with open(file_path, "rb") as file:
        file_content = file.read()
        file.seek(0)
        file_type = imghdr.what(None, file_content)
        print(file_type)
        if file_type != "jpeg" and file_type != "jpg" and file_type != "png":
            logger.error(
                f"Unsupported file type for image {file.filename}: {file_type}"
            )
            return
        try:
            # 使用Pillow打开图片并调整大小
            img = Image.open(io.BytesIO(file_content))
            img.thumbnail(size)

            # 创建一个新的PDF页面
            img_packet = io.BytesIO()
            img_canvas = canvas.Canvas(img_packet, pagesize=letter)
            if file_type == "png":
                jpeg_bytesio = convert_png_to_jpeg_bytesio(io.BytesIO(file_content))
            else:
                jpeg_bytesio = io.BytesIO(file_content)
            img_canvas.drawImage(
                ImageReader(jpeg_bytesio),
                pos_x,
                pos_y,
                width=size[0],
                height=size[1],
            )
            img_canvas.save()
            img_packet.seek(0)
            img_pdf = PdfReader(img_packet)
            page.merge_page(img_pdf.pages[0])
        except Exception as e:
            logger.error(f"Failed to process image {file.filename} {str(e)[:100]}")
            # logger.error(f"Failed to process image {file.filename}: {e}")


# 插入身份证照片
async def add_image_to_pdf(
    file: UploadFile,
    page: PageObject,
    pos_x: int,
    pos_y: int,
    size: tuple,
):
    if file:
        await file.seek(0)
        file_content = await file.read()
        file_type = imghdr.what(None, file_content)
        if file_type != "jpeg" and file_type != "jpg" and file_type != "png":
            logger.error(
                f"Unsupported file type for image {file.filename}: {file_type}"
            )
            return
        try:
            # 使用Pillow打开图片并调整大小
            img = Image.open(io.BytesIO(file_content))
            img.thumbnail(size)

            # 创建一个新的PDF页面
            img_packet = io.BytesIO()
            img_canvas = canvas.Canvas(img_packet, pagesize=letter)
            if file_type == "png":
                jpeg_bytesio = convert_png_to_jpeg_bytesio(io.BytesIO(file_content))
            else:
                jpeg_bytesio = io.BytesIO(file_content)
            img_canvas.drawImage(
                ImageReader(jpeg_bytesio),
                pos_x,
                pos_y,
                width=size[0],
                height=size[1],
            )
            img_canvas.save()

            img_packet.seek(0)
            img_pdf = PdfReader(img_packet)
            page.merge_page(img_pdf.pages[0])
        except Exception as e:
            logger.error(f"Failed to process image {file.filename} {str(e)[:100]}")
            # logger.error(f"Failed to process image {file.filename}: {e}")
