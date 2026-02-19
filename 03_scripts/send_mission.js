#!/usr/bin/env node

/**
 * Project Sunshine - Mission Auto-Sender
 * 
 * Usage: node send_mission.js [mission_file.json]
 * Example: node send_mission.js mission_cherry.json
 */

const nodemailer = require('nodemailer');
const fs = require('fs');
const path = require('path');

// Default mission file path
const MISSION_DIR = '/Users/al02399300/.n8n-files/sunshine/missions/';

// Get mission file from command line argument
const missionFile = process.argv[2] || 'mission_cherry.json';
const missionPath = missionFile.startsWith('/')
    ? missionFile
    : path.join(MISSION_DIR, missionFile);

console.log('📦 Project Sunshine Mission Auto-Sender');
console.log('=====================================\n');

// Read mission JSON
console.log(`📄 Reading mission file: ${missionPath}`);

if (!fs.existsSync(missionPath)) {
    console.error(`❌ Error: Mission file not found: ${missionPath}`);
    process.exit(1);
}

const missionData = fs.readFileSync(missionPath, 'utf8');
const mission = JSON.parse(missionData);

console.log(`✅ Mission loaded: ${mission.meta.target}`);
console.log(`📧 Subject: ${mission.content.subject}\n`);

// Create transporter
const transporter = nodemailer.createTransport({
    host: 'smtp.gmail.com',
    port: 465,
    secure: true, // SSL/TLS
    auth: {
        user: 'sepalsepal@gmail.com',
        pass: 'qviu ndrf qxus bvxo' // Gmail App Password
    }
});

// Email options
const mailOptions = {
    from: 'sepalsepal@gmail.com',
    to: 'laxa674noyi@post.wordpress.com',
    subject: mission.content.subject,
    html: mission.content.body
};

// Send email
console.log('🚀 Sending email to WordPress...\n');

transporter.sendMail(mailOptions, (error, info) => {
    if (error) {
        console.error('❌ Error sending email:', error);
        process.exit(1);
    }

    console.log('✅ Email sent successfully!');
    console.log(`📬 Message ID: ${info.messageId}`);
    console.log(`📨 Response: ${info.response}\n`);
    console.log('🎉 Mission complete! Check WordPress in 1-3 minutes.');
});
