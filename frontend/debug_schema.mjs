import { neon } from '@neondatabase/serverless';

const DATABASE_URL = "postgresql://neondb_owner:npg_PpdcmHfn73bl@ep-sweet-term-adm0rzzh-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require";
const sql = neon(DATABASE_URL);

async function checkSchema() {
    try {
        const columns = await sql`
      SELECT column_name, data_type 
      FROM information_schema.columns 
      WHERE table_name = 'horses'
      ORDER BY ordinal_position;
    `;
        console.log("Columns in 'horses' table:");
        columns.forEach(col => {
            console.log(`- ${col.column_name}: ${col.data_type}`);
        });
    } catch (err) {
        console.error("Error checking schema:", err);
    }
}

checkSchema();
